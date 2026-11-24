/* =========================================================
   پازل قصه‌های پرنده — site.js
   منطق پیشرفت پازل، بازگشت از قصه، و انتخاب عکس
   (ساختار حفظ‌شده از نسخهٔ موجود؛ فایل اصلی ZIP در دسترس نبود
   و این پیاده‌سازی بر پایهٔ همان رفتار بازسازی شده است.)
   ========================================================= */
(function () {
  "use strict";

  /* ---------- ثابت‌ها ---------- */
  var STORY_IDS = ["pishi", "dal", "florence", "medad"];
  var TOTAL = STORY_IDS.length;                 // ۴ قصه
  var FRAME_SRC = [
    "assets/parandeh-storybird-0.webp",         // طرح دوخته‌شده، چشم‌بسته
    "assets/parandeh-storybird-1.webp",         // چشم باز می‌کند
    "assets/parandeh-storybird-2.webp",         // بال می‌گیرد
    "assets/parandeh-storybird-3.webp",         // از صفحه بلند می‌شود
    "assets/parandeh-storybird-4.webp"          // پرواز
  ];
  var FRAME_ALT = [
    "تصویر پازل: پرنده‌ی دوخته‌شده روی کتاب؛ هنوز چشم‌هایش بسته است",
    "تصویر پازل: پرنده چشم‌هایش را باز کرده است",
    "تصویر پازل: پرنده بال‌هایش را باز کرده است",
    "تصویر پازل: پرنده از صفحه‌ی کتاب بلند شده است",
    "تصویر پازل: پرنده در آسمان پرواز می‌کند"
  ];
  var LS_KEY = "parandeh-puzzle-v1";
  var DAY = 86400000;
  var RETENTION_DAYS = 7;                       // ماندگاری ۷ روز در همین مرورگر
  var COMPLETION_THRESHOLD = 0.75;              // آستانهٔ ۷۵٪ — فقط معیار پیش‌نمایش فعلی
  var MAX_PHOTO_BYTES = 10 * 1024 * 1024;       // ۱۰ مگابایت
  var PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];
  var RETURN_GRACE_MS = 1200;                   // بازگشت آنی = تازه کلیک شده، نتیجه نیست

  /* اعداد فارسی */
  function faNum(n) {
    var map = "۰۱۲۳۴۵۶۷۸۹";
    return String(n).replace(/\d/g, function (d) { return map[+d]; });
  }

  /* ---------- وضعیت ---------- */
  var state = load();

  function defaultState() {
    return { done: {}, pending: null, ts: 0, photo: null };
  }
  function load() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (!raw) return defaultState();
      var s = JSON.parse(raw);
      if (!s || typeof s !== "object") return defaultState();
      if (Date.now() - (s.ts || 0) > RETENTION_DAYS * DAY) {
        localStorage.removeItem(LS_KEY);
        return defaultState();
      }
      return { done: s.done || {}, pending: s.pending || null, ts: s.ts || 0, photo: s.photo || null };
    } catch (e) { return defaultState(); }
  }
  function save() {
    try {
      state.ts = Date.now();
      // پیش‌نمایش عکس فقط برای همین نشست نگه داشته می‌شود؛ فایل روی دستگاه می‌ماند
      var persist = { done: state.done, pending: state.pending, ts: state.ts };
      localStorage.setItem(LS_KEY, JSON.stringify(persist));
    } catch (e) { /* حافظه پر/غیرفعال */ }
  }

  function heardCount() {
    return STORY_IDS.filter(function (id) { return !!state.done[id]; }).length;
  }

  /* ---------- عناصر ---------- */
  var $ = function (sel) { return document.querySelector(sel); };
  var bigImg     = $("#puzzleBig");
  var labelEl    = $("#progressLabel");
  var barEl      = $("#progressBar");
  var fillEl     = $("#progressFill");
  var msgEl      = $("#puzzleMessage");
  var inlineBtn  = $("#pickPhotoInline");
  var thumbs     = Array.prototype.slice.call(document.querySelectorAll(".stage-thumb"));
  var cards      = {};
  Array.prototype.forEach.call(document.querySelectorAll(".story-card"), function (c) {
    cards[c.getAttribute("data-story")] = c;
  });

  /* ---------- به‌روزرسانی نما ---------- */
  function render() {
    var n = heardCount();

    if (bigImg.getAttribute("src") !== FRAME_SRC[n]) {
      bigImg.src = FRAME_SRC[n];
    }
    bigImg.alt = FRAME_SRC && FRAME_ALT[n];

    labelEl.textContent = faNum(n) + " از " + faNum(TOTAL) + " قصه شنیده شده";
    fillEl.style.width = Math.round((n / TOTAL) * 100) + "%";
    barEl.setAttribute("aria-valuenow", String(n));

    thumbs.forEach(function (t, i) {
      // نشانگر مرحله: تا وقتی آن مرحله پر نشده، فقط همان برشِ مات دیده می‌شود
      t.classList.toggle("is-done", n >= i + 1);
    });

    // پیام و دکمهٔ «انتخاب عکس» کنار پازل، فقط پس از کامل شدن
    if (n === TOTAL) {
      msgEl.hidden = false;
      msgEl.textContent = "پرنده‌ات کامل شد!";
      inlineBtn.hidden = false;
    } else {
      msgEl.hidden = true;
      msgEl.textContent = "";
      inlineBtn.hidden = true;
    }

    // گزینهٔ «ادامهٔ همین قصه» برای قصهٔ نیمه‌تمام
    Object.keys(cards).forEach(function (id) {
      var btn = cards[id].querySelector(".js-continue");
      if (!btn) return;
      var show = state.pending === id && !state.done[id];
      btn.hidden = !show;
      if (show) btn.setAttribute("href-target", storyUrl(id));
    });

    // پیش‌نمایش عکس در بنر پایین
    var pv = $("#photoPreview");
    if (state.photo && pv) { pv.src = state.photo; pv.hidden = false; }
    else if (pv) { pv.hidden = true; pv.removeAttribute("src"); }
  }

  function storyUrl(id) {
    var a = cards[id] && cards[id].querySelector(".story-link");
    return a ? a.href : "#";
  }

  function markHeard(id) {
    if (!state.done[id]) {
      state.done[id] = Date.now();
    }
    if (state.pending === id) state.pending = null;
    save();
    render();
  }

  /* ---------- ثبت نتیجهٔ بازگشت از قصه ---------- */
  /*
     پارامترهای ممکن (از اپ / player هنگام بازگشت):
       ?story=<id>&result=finished|partial|invalid
     یا پیام postMessage با ساختار {type:"story-result", story, result}
     - finished → قصهٔ تازه شمرده می‌شود (تکراری دوباره شمرده نمی‌شود)
     - partial  → پیشرفت ثابت می‌ماند + «ادامهٔ همین قصه»
     - invalid  → پیام فارسی، بدون تغییر پیشرفت
     - بازگشت بدون نتیجه → پیشرفت قبلی حفظ می‌شود
  */
  function handleResult(params) {
    var id = params.get("story");
    var res = params.get("result");
    if (!id || STORY_IDS.indexOf(id) === -1) return false;

    if (res === "finished") {
      markHeard(id);
      flash("آفرین! «" + cardTitle(id) + "» شنیده شد.");
      return true;
    }
    if (res === "partial") {
      state.pending = id;           // پیشرفت ثابت می‌ماند
      save();
      render();
      flash("این قصه هنوز تمام نشده؛ هر وقت خواستی ادامه بده.");
      return true;
    }
    if (res === "invalid") {
      flash("نتیجهٔ این قصه معتبر نبود؛ لطفاً دوباره گوش بده.");
      return true;
    }
    return false; // بازگشت بدون نتیجه
  }

  function flash(text) {
    msgEl.hidden = false;
    msgEl.textContent = text;
    clearTimeout(flash._t);
    flash._t = setTimeout(render, 3500); // بعد از چند لحظه به نمای استاندارد برمی‌گردد
  }

  function cardTitle(id) {
    var h = cards[id] && cards[id].querySelector(".story-name");
    return h ? h.textContent.trim() : "";
  }

  /* کلیک روی کارت = شروع/ادامهٔ همان قصه (ثبت pending) */
  Object.keys(cards).forEach(function (id) {
    var link = cards[id].querySelector(".story-link");
    if (link) {
      link.addEventListener("click", function () {
        if (!state.done[id]) {
          state.pending = id;
          save();
        }
      });
    }
    var cont = cards[id].querySelector(".js-continue");
    if (cont) {
      cont.addEventListener("click", function () {
        window.open(storyUrl(id), "_blank", "noopener");
      });
    }
  });

  /* دریافت نتیجه از طریق URL */
  (function fromQuery() {
    var q = new URLSearchParams(window.location.search);
    if (handleResult(q)) {
      // پاک‌کردن پارامترها از آدرس، بدون افزودن به تاریخچه
      history.replaceState(null, "", window.location.pathname);
    }
  })();

  /* دریافت نتیجه از طریق postMessage (بازگشت از تب/player) */
  window.addEventListener("message", function (ev) {
    var d = ev.data;
    if (!d || d.type !== "story-result") return;
    var p = new URLSearchParams();
    p.set("story", String(d.story || ""));
    p.set("result", String(d.result || ""));
    handleResult(p);
  });

  /* اگر تب بعد از باز بودن قصه فعال شد و نتیجه‌ای در URL نبود،
     پیشرفت قبلی باید دست‌نخورده بماند — اینجا فقط render می‌کنیم. */
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) render();
  });

  /* ---------- اسکرول نرم «بزن بریم» ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-scroll]"), function (a) {
    a.addEventListener("click", function (e) {
      var target = document.querySelector(a.getAttribute("href"));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  /* ---------- پنجرهٔ مشترک انتخاب عکس ---------- */
  var modal   = $("#photoModal");
  var input   = $("#photoInput");
  var chooseB = $("#chooseFileBtn");
  var removeB = $("#removePhotoBtn");
  var mPrev   = $("#modalPreview");
  var mMsg    = $("#modalMsg");
  var lastFocus = null;

  Array.prototype.forEach.call(document.querySelectorAll(".js-pick-photo"), function (b) {
    b.addEventListener("click", openModal);
  });
  $("#modalClose").addEventListener("click", closeModal);
  Array.prototype.forEach.call(modal.querySelectorAll("[data-close]"), function (x) {
    x.addEventListener("click", closeModal);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) closeModal();
  });

  function openModal() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    setMsg("");
    showPreview(state.photo, !!state.photo);
    chooseB.focus();
  }
  function closeModal() {
    modal.hidden = true;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  chooseB.addEventListener("click", function () { input.click(); });
  input.addEventListener("change", function () {
    var f = input.files && input.files[0];
    if (!f) return;
    if (PHOTO_TYPES.indexOf(f.type) === -1) {
      showPreview(null, false);
      setMsg("فقط فایل JPG، PNG یا WebP پذیرفته می‌شود.", true);
      input.value = "";
      return;
    }
    if (f.size > MAX_PHOTO_BYTES) {
      showPreview(null, false);
      setMsg("حجم فایل بیشتر از ۱۰ مگابایت است؛ لطفاً عکس سبک‌تری انتخاب کن.", true);
      input.value = "";
      return;
    }
    var url = URL.createObjectURL(f);   // فایل روی دستگاه می‌ماند؛ جایی آپلود نمی‌شود
    var probe = new Image();
    probe.onload = function () {
      state.photo = url;
      save();
      render();
      showPreview(url, true);
      setMsg("عکس انتخاب شد. آفرین!", false);
    };
    probe.onerror = function () {
      URL.revokeObjectURL(url);
      showPreview(null, false);
      setMsg("این فایل خراب است و باز نمی‌شود؛ لطفاً عکس دیگری انتخاب کن.", true);
    };
    probe.src = url;
    input.value = "";
  });

  removeB.addEventListener("click", function () {
    if (state.photo) { try { URL.revokeObjectURL(state.photo); } catch (e) {} }
    state.photo = null;
    save();
    render();
    showPreview(null, false);
    setMsg("تصویر برداشته شد.", false);
  });

  function showPreview(src, ok) {
    removeB.hidden = !ok;
    if (ok) {
      mPrev.src = src; mPrev.hidden = false;
    } else {
      mPrev.hidden = true; mPrev.removeAttribute("src");
    }
  }
  function setMsg(text, isErr) {
    mMsg.textContent = text || "";
    mMsg.classList.toggle("err", !!isErr);
    mMsg.classList.toggle("ok", !!text && !isErr);
  }

  /* ---------- شروع ---------- */
  render();
})();
