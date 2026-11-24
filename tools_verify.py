#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the landing page behaviour & layout with Playwright."""
import subprocess, sys, time, os, signal

srv = subprocess.Popen([sys.executable, "-m", "http.server", "8099"],
                       cwd="/workspace", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8099/index.html"
ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: ok = False

with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------- desktop 1440 ----------
    ctx = b.new_context(viewport={"width":1440,"height":900}, locale="fa")
    pg = ctx.new_page()
    pg.goto(BASE)
    check("lang fa / dir rtl", pg.evaluate("document.documentElement.lang")=="fa" and pg.evaluate("document.documentElement.dir")=="rtl")
    check("no horizontal scroll @1440", pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))

    # header: parandeh right, zipad left
    r = pg.evaluate("""()=>{const a=document.querySelector('.brand-main img').getBoundingClientRect();
        const z=document.querySelector('.brand-zipad img').getBoundingClientRect();
        return {ar:a.right,zr:z.right}}""")
    check("logo parandeh راست، زیپاد چپ", r["ar"] > r["zr"])

    # hero panel on right side of banner image (desktop overlay)
    hp = pg.evaluate("""()=>{const h=document.querySelector('.hero-img').getBoundingClientRect();
        const p=document.querySelector('.hero-panel').getBoundingClientRect();
        return {overlap:p.top>=h.top-2 && p.bottom<=h.bottom+2, rightSide:(p.right-p.left)>0 && (h.right-p.left)<p.width*1.25 && (p.right-h.left)>h.width*0.5}}""")
    check("پنل سفید متن روی سمت راست تصویر بنر (دسکتاپ)", hp["overlap"] and hp["rightSide"])

    # puzzle desktop: big image right, info left
    pz = pg.evaluate("""()=>{const f=document.querySelector('.puzzle-figure').getBoundingClientRect();
        const i=document.querySelector('.puzzle-info').getBoundingClientRect();
        return f.left>i.right-40 || f.left>i.left}""")
    pf = pg.evaluate("""()=>{const f=document.querySelector('.puzzle-figure').getBoundingClientRect().left;
        const i=document.querySelector('.puzzle-info').getBoundingClientRect().left;
        return {f:f,i:i}}""")
    check("تصویر بزرگ پازل راست، توضیح/پیشرفت چپ (دسکتاپ)", pf["f"] > pf["i"])

    # stories grid single? no -> 4 columns RTL order
    order = pg.evaluate("""()=>[...document.querySelectorAll('.story-card')].map(c=>({id:c.dataset.story,x:c.getBoundingClientRect().left}))""")
    xs = sorted([o["x"] for o in order])
    ids_by_x_desc = [o["id"] for o in sorted(order, key=lambda o:-o["x"])]
    check("چهارستونه و راست‌به‌چپ: پیشی، دال، فلورانس، مداد", ids_by_x_desc==["pishi","dal","florence","medad"])
    cols = pg.evaluate("getComputedStyle(document.querySelector('.story-grid')).gridTemplateColumns.split(' ').length")
    check("4 ستون در دسکتاپ", cols==4)

    # initial state
    lab = pg.text_content("#progressLabel").strip()
    check("حالت اولیه «۰ از ۴ قصه شنیده شده»", lab=="۰ از ۴ قصه شنیده شده")
    src0 = pg.get_attribute("#puzzleBig","src")
    check("قاب ۰ در ابتدا", src0.endswith("parandeh-storybird-0.webp"))
    check("دکمهٔ انتخاب عکس کنار پازل در ابتدا مخفی", pg.evaluate("!document.querySelector('#pickPhotoInline').hidden")==False)
    check("پیام مخفی در ابتدا", pg.evaluate("document.querySelector('#puzzleMessage').hidden"))

    # opening a story link alone must NOT advance: simulate click capture
    pg.evaluate("""()=>{const a=document.querySelector('[data-story=pishi] .story-link');
        a.addEventListener('click',e=>e.preventDefault());}""")
    pg.click("[data-story=pishi] .story-link")
    check("باز کردن لینک قصه به‌تنهایی پیشرفت ایجاد نمی‌کند", pg.text_content("#progressLabel").strip()=="۰ از ۴ قصه شنیده شده")

    # stage progression via result param
    def finish(story):
        pg.goto(BASE + f"?story={story}&result=finished")
    finish("pishi");   check("قصهٔ ۱ → قاب ۱", pg.get_attribute("#puzzleBig","src").endswith("-1.webp") and pg.text_content("#progressLabel").strip()=="۱ از ۴ قصه شنیده شده")
    finish("dal");     check("قصهٔ ۲ → قاب ۲", pg.get_attribute("#puzzleBig","src").endswith("-2.webp"))
    finish("florence");check("قصهٔ ۳ → قاب ۳", pg.get_attribute("#puzzleBig","src").endswith("-3.webp"))
    finish("medad");   check("قصهٔ ۴ → قاب ۴ پرواز", pg.get_attribute("#puzzleBig","src").endswith("-4.webp"))
    check("پیام «پرنده‌ات کامل شد!»", "پرنده‌ات کامل شد!" in pg.text_content("#puzzleMessage"))
    check("دکمهٔ انتخاب عکس کنار پازل ظاهر شد", pg.evaluate("!document.querySelector('#pickPhotoInline').hidden"))
    fillw = pg.evaluate("document.querySelector('#progressFill').style.width")
    check("نوار پیشرفت ۱۰۰٪", fillw=="100%")

    # duplicate story not counted again
    finish("pishi")
    check("قصهٔ تکراری دوباره شمرده نمی‌شود", pg.text_content("#progressLabel").strip()=="۴ از ۴ قصه شنیده شده")

    # partial keeps progress + continue button
    pg.goto(BASE + "?story=dal&result=partial")
    check("قصهٔ نیمه‌تمام: پیشرفت ثابت", pg.text_content("#progressLabel").strip()=="۴ از ۴ قصه شنیده شده")
    cont_visible = pg.evaluate("!document.querySelector('[data-story=dal] .js-continue').hidden")
    # dal is done so continue hidden; test partial on fresh context below
    ctx.close()

    # ---------- fresh context: partial/invalid/no-result ----------
    ctx2 = b.new_context(viewport={"width":1440,"height":900})
    pg2 = ctx2.new_page()
    pg2.goto(BASE + "?story=florence&result=partial")
    check("با قصهٔ نیمه‌تمام گزینهٔ «ادامهٔ همین قصه» ظاهر می‌شود", pg2.evaluate("!document.querySelector('[data-story=florence] .js-continue').hidden"))
    check("پیشرفت با partial ثابت می‌ماند (۰)", pg2.text_content("#progressLabel").strip()=="۰ از ۴ قصه شنیده شده")
    pg2.goto(BASE + "?story=florence&result=invalid")
    msg = pg2.text_content("#puzzleMessage")
    check("نتیجهٔ نامعتبر پیام فارسی دارد", "معتبر نبود" in msg)
    pg2.goto(BASE + "?story=medad&result=finished")
    pg2.goto(BASE)  # normal return without result
    check("بازگشت عادی بدون نتیجه، پیشرفت قبلی را حفظ می‌کند", pg2.text_content("#progressLabel").strip()=="۱ از ۴ قصه شنیده شده")

    # thumbs are not buttons and clicks do nothing
    tg = pg2.evaluate("""()=>{const t=[...document.querySelectorAll('.stage-thumb')];
        const before=document.querySelector('#puzzleBig').getAttribute('src');
        t.forEach(x=>x.dispatchEvent(new MouseEvent('click',{bubbles:true})));
        return {tag:t[0].tagName, changed:document.querySelector('#puzzleBig').getAttribute('src')!==before};}""")
    check("تصاویر کوچک دکمه نیستند", tg["tag"]=="LI")
    check("کلیک روی آن‌ها تصویر بزرگ را تغییر نمی‌دهد", not tg["changed"])

    # photo modal shared by both buttons
    pg2.click(".photobanner .js-pick-photo")
    check("مودال باز می‌شود", pg2.evaluate("!document.querySelector('#photoModal').hidden"))
    pg2.keyboard.press("Escape")
    check("Esc مودال را می‌بندد", pg2.evaluate("document.querySelector('#photoModal').hidden"))

    # valid image
    png = "/tmp/test-photo.png"
    from PIL import Image
    Image.new("RGB",(60,60),(120,60,200)).save(png)
    pg2.click("#pickPhotoInline")
    pg2.set_input_files("#photoInput", png)
    pg2.wait_for_selector("#modalPreview:not([hidden])")
    check("عکس معتبر: پیش‌نمایش و «برداشتن تصویر»", pg2.evaluate("!document.querySelector('#removePhotoBtn').hidden"))
    pg2.click("#modalClose")
    check("پیش‌نمایش عکس در بنر پایین", pg2.evaluate("!document.querySelector('#photoPreview').hidden"))
    # invalid type
    bad = "/tmp/bad.txt"
    open(bad,"w").write("hello")
    pg2.click(".photobanner .js-pick-photo")
    pg2.set_input_files("#photoInput", bad)
    m = pg2.text_content("#modalMsg")
    check("فایل نامعتبر: پیام فارسی", "JPG" in m or "پذیرفته" in m)
    # corrupt image with valid mime
    import shutil
    corrupt="/tmp/corrupt.png"; open(corrupt,"wb").write(b"\x89PNG\r\n\x1a\n" + b"garbage"*50)
    pg2.set_input_files("#photoInput", corrupt)
    pg2.wait_for_function("document.querySelector('#modalMsg').textContent.length>0")
    m2 = pg2.text_content("#modalMsg")
    check("فایل خراب: پیام فارسی مناسب", "خراب" in m2)
    # remove photo
    pg2.set_input_files("#photoInput", png)
    pg2.wait_for_selector("#modalPreview:not([hidden])")
    pg2.click("#removePhotoBtn")
    check("«برداشتن تصویر» کار می‌کند", pg2.evaluate("document.querySelector('#modalPreview').hidden"))
    pg2.keyboard.press("Escape")
    ctx2.close()

    # persistence 7 days: set old ts
    ctx3 = b.new_context(viewport={"width":1440,"height":900})
    pg3 = ctx3.new_page()
    pg3.goto(BASE)
    pg3.goto(BASE + "?story=pishi&result=finished")
    pg3.evaluate("""()=>{const k='parandeh-puzzle-v1';const s=JSON.parse(localStorage.getItem(k));
        s.ts=Date.now()-8*86400000;localStorage.setItem(k,JSON.stringify(s));}""")
    pg3.goto(BASE)
    check("پیشرفت پس از ۷ روز منقضی می‌شود", pg3.text_content("#progressLabel").strip()=="۰ از ۴ قصه شنیده شده")
    ctx3.close()

    # ---------- mobile 390 ----------
    ctx4 = b.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True)
    pg4 = ctx4.new_page()
    pg4.goto(BASE)
    check("بدون اسکرول افقی @390", pg4.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
    # hero: image top, text+button below, full-width button
    lay = pg4.evaluate("""()=>{const h=document.querySelector('.hero-img').getBoundingClientRect();
        const p=document.querySelector('.hero-panel').getBoundingClientRect();
        const btn=document.querySelector('.btn-hero').getBoundingClientRect();
        return {imgAbove:h.bottom<=p.top+2, full:Math.abs(btn.width-p.width)<=1.5||btn.width>=p.width-2.5}}""")
    check("موبایل: تصویر بنر بالا، متن پایین", lay["imgAbove"])
    check("موبایل: دکمهٔ تمام‌عرض", lay["full"])
    # puzzle order: title/desc -> image+thumbs -> progress+button
    ord_ = pg4.evaluate("""()=>{const y=s=>document.querySelector(s).getBoundingClientRect().top+scrollY;
        return {title:y('.puzzle-info .section-title'), desc:y('.puzzle-desc'), fig:y('.puzzle-figure'),
                thumbs:y('.puzzle-stages'), prog:y('.puzzle-progressbox') }}""")
    check("ترتیب موبایل: عنوان/توضیح ← تصویر/مراحل ← پیشرفت",
          ord_["title"]<=ord_["desc"] and ord_["fig"]>=ord_["desc"]-1 and ord_["prog"]>=ord_["thumbs"]-1 and ord_["prog"]>=ord_["fig"]-1)
    # cards stacked, cover right
    st = pg4.evaluate("""()=>{const g=getComputedStyle(document.querySelector('.story-grid')).gridTemplateColumns.split(' ').length;
        const c=document.querySelector('[data-story=pishi]');
        const img=c.querySelector('.story-cover').getBoundingClientRect();
        const name=c.querySelector('.story-name').getBoundingClientRect();
        return {cols:g, imgRight:img.left>name.left}}""")
    check("موبایل: کارت‌ها زیر هم", st["cols"]==1)
    check("موبایل: تصویر قصه سمت راست کارت", st["imgRight"])
    pg4.screenshot(path="/workspace/design/mobile.png", full_page=True)
    ctx4.close()

    pgd = b.new_page(viewport={"width":1440,"height":900})
    pgd.goto(BASE)
    pgd.goto(BASE + "?story=pishi&result=finished")
    pgd.goto(BASE + "?story=dal&result=finished")
    pgd.goto(BASE + "?story=florence&result=finished")
    pgd.goto(BASE + "?story=medad&result=finished")
    pgd.screenshot(path="/workspace/design/desktop.png", full_page=True)
    pgd.close()

    b.close()

srv.send_signal(signal.SIGINT)
print("RESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
