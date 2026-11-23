#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام رنگ — نئی اشاعت شامل کرنے کا اسکرپٹ

PDF سے نئی اشاعت:
    python3 tools/add_issue.py "C:/میگزین/feb.pdf" --slug 2025-02 \
        --title "فروری ایڈیشن" --period "فروری 2025"

پہلے سے بنی تصاویر کے فولڈر سے (poppler کے بغیر):
    python3 tools/add_issue.py --images "C:/تصاویر" --slug 2025-02 --title "..."

دیگر کام:
    python3 tools/add_issue.py --rebuild          # تمام HTML صفحات اور روابط دوبارہ بنائیں
    python3 tools/add_issue.py --remove 2025-02   # کوئی اشاعت ہٹائیں

ضرورت: Python 3 اور poppler (pdftoppm, pdfinfo) — صرف PDF موڈ کے لیے۔
"""
import argparse, glob, html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "issues.js")
SITE = "نظام رنگ"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lalezar'
         '&family=Noto+Naskh+Arabic:wght@400;700&family=Noto+Nastaliq+Urdu:wght@400;600&display=swap">')
FAVICON = ('<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E'
           '%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230b3322%27/%3E%3Cpath d=%27M16 9c-3-2-7-2-10-1v14c3-1 7-1 10 1 3-2 7-2 10-1V8c-3-1-7-1-10 1z%27 '
           'fill=%27none%27 stroke=%27%23e0be72%27 stroke-width=%272%27 stroke-linejoin=%27round%27/%3E%3C/svg%3E">')


def esc(t):
    return html.escape(str(t), quote=True)


def pad(n):
    return "%02d" % n


# ---------------------------------------------------------------- data
def load():
    if not os.path.exists(DATA):
        return []
    txt = open(DATA, encoding="utf-8").read()
    m = re.search(r"window\.ISSUES\s*=\s*(\[.*\])\s*;?\s*$", txt, re.S)
    if not m:
        sys.exit("data/issues.js پڑھا نہیں جا سکا")
    return json.loads(m.group(1))


def save(issues):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    body = json.dumps(issues, ensure_ascii=False, indent=2)
    open(DATA, "w", encoding="utf-8").write(
        "/* اشاعتوں کی فہرست — ترتیب بدلنے یا عنوان درست کرنے کے لیے اسی فائل میں ترمیم کریں */\n"
        "window.ISSUES = " + body + ";\n")


# ---------------------------------------------------------------- rendering
def need(tool):
    if not shutil.which(tool):
        sys.exit("'%s' نہیں ملا۔ poppler انسٹال کریں (Windows: poppler for windows، Mac: brew install poppler، "
                 "Linux: apt install poppler-utils) یا --images موڈ استعمال کریں۔" % tool)


def pdf_meta(pdf):
    need("pdfinfo")
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", out).group(1))
    w, h = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", out).groups()
    return pages, float(w) / float(h)


def pdftoppm(pdf, outdir, prefix, width, quality, first=None, last=None):
    cmd = ["pdftoppm", "-jpeg", "-jpegopt", "quality=%d,progressive=y,optimize=y" % quality,
           "-scale-to-x", str(width), "-scale-to-y", "-1"]
    if first:
        cmd += ["-f", str(first), "-l", str(last or first)]
    subprocess.run(cmd + [pdf, os.path.join(outdir, prefix)], check=True, capture_output=True)
    return sorted(glob.glob(os.path.join(outdir, prefix + "-*.jpg")))


def can_pil():
    try:
        import PIL  # noqa
        return True
    except ImportError:
        return False


def can_webp():
    try:
        from PIL import features
        return bool(features.check("webp"))
    except Exception:
        return False


def save_img(im, path, ext, q):
    if ext == "webp":
        im.save(path, "WEBP", quality=q, method=6)
    else:
        im.save(path, "JPEG", quality=q, optimize=True, progressive=True)


def resized(im, w):
    from PIL import Image
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im


def render_pdf(pdf, imgdir, width, quality, ext, cover):
    need("pdftoppm")
    tmp = tempfile.mkdtemp()
    try:
        if ext == "webp":                      # PNG سے براہِ راست WebP: دوہری کمپریشن نہیں
            from PIL import Image
            subprocess.run(["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", "-1",
                            pdf, os.path.join(tmp, "p")], check=True, capture_output=True)
            files = sorted(glob.glob(os.path.join(tmp, "p-*.png")))
            for i, f in enumerate(files, 1):
                im = Image.open(f).convert("RGB")
                save_img(im, os.path.join(imgdir, "page-%s.webp" % pad(i)), ext, quality)
                save_img(resized(im, 260), os.path.join(imgdir, "thumb-%s.webp" % pad(i)), ext, 60)
                if i == cover:
                    save_img(resized(im, 640), os.path.join(imgdir, "cover.webp"), ext, 75)
                im.close(); os.remove(f)
            return len(files)
        pages = pdftoppm(pdf, tmp, "p", width, quality)
        for i, f in enumerate(pages, 1):
            shutil.move(f, os.path.join(imgdir, "page-%s.jpg" % pad(i)))
        for i, f in enumerate(pdftoppm(pdf, tmp, "t", 260, 70), 1):
            shutil.move(f, os.path.join(imgdir, "thumb-%s.jpg" % pad(i)))
        shutil.move(pdftoppm(pdf, tmp, "c", 640, 82, first=cover)[0], os.path.join(imgdir, "cover.jpg"))
        return len(pages)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def render_images(src, imgdir, width, quality, ext, cover):
    files = sorted(f for f in glob.glob(os.path.join(src, "*")) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    if not files:
        sys.exit("اس فولڈر میں کوئی تصویر نہیں ملی")
    aspect = None
    cover = min(cover, len(files))
    if not can_pil():
        if not all(f.lower().endswith((".jpg", ".jpeg")) for f in files):
            sys.exit("PNG/WEBP کے لیے Pillow درکار ہے (pip install pillow)، یا JPG تصاویر دیں")
        for i, f in enumerate(files, 1):
            shutil.copy(f, os.path.join(imgdir, "page-%s.jpg" % pad(i)))
            shutil.copy(f, os.path.join(imgdir, "thumb-%s.jpg" % pad(i)))
            if i == cover:
                shutil.copy(f, os.path.join(imgdir, "cover.jpg"))
        return len(files), None
    from PIL import Image
    for i, f in enumerate(files, 1):
        im = Image.open(f).convert("RGB")
        aspect = aspect or im.width / im.height
        save_img(resized(im, width), os.path.join(imgdir, "page-%s.%s" % (pad(i), ext)), ext, quality)
        save_img(resized(im, 260), os.path.join(imgdir, "thumb-%s.%s" % (pad(i), ext)), ext, 60 if ext == "webp" else 70)
        if i == cover:
            save_img(resized(im, 640), os.path.join(imgdir, "cover.%s" % ext), ext, 75 if ext == "webp" else 82)
    return len(files), aspect


# ---------------------------------------------------------------- HTML
def head(title, desc, img="", extra=""):
    og = '<meta property="og:image" content="%s">\n' % esc(img) if img else ""
    return ('<!DOCTYPE html>\n<html lang="ur" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<meta property="og:title" content="%s">\n%s%s\n%s\n'
            '<link rel="stylesheet" href="../../assets/css/style.css">\n%s</head>\n'
            % (esc(title), esc(desc), esc(title), og, FAVICON, FONTS, extra))


SCRIPTS = ('<script src="../../data/issues.js"></script>\n<script src="../../assets/js/common.js"></script>\n'
           '<script src="../../assets/js/viewer.js"></script>\n')


def write_issue_html(issue):
    slug, n, title = issue["slug"], issue["pages"], issue["title"]
    ext = issue.get("ext", "jpg")
    d = os.path.join(ROOT, "issues", slug)
    os.makedirs(d, exist_ok=True)
    desc = "%s — %s" % (SITE, title)

    nav = "".join('<a href="page-%s.html">%d</a>' % (pad(i), i) for i in range(1, n + 1))
    ns = '<noscript><div class="ns"><a href="../../index.html">تمام اشاعتیں</a> %s</div></noscript>\n' % nav
    idx = (head("%s | %s" % (title, SITE), desc, "images/cover." + ext) +
           '<body class="viewer" data-mode="app" data-issue="%s">\n'
           '<div id="stage"><div id="book" class="book"></div></div>\n%s%s</body>\n</html>\n'
           % (esc(slug), ns, SCRIPTS))
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(idx)

    for i in range(1, n + 1):
        rel = ""
        if i > 1:
            rel += '<link rel="prev" href="page-%s.html">\n' % pad(i - 1)
        if i < n:
            rel += '<link rel="next" href="page-%s.html">\n' % pad(i + 1)
        nv = ""
        if i > 1:
            nv += '<a href="page-%s.html">پچھلا</a> ' % pad(i - 1)
        nv += '<a href="index.html">فہرست</a>'
        if i < n:
            nv += ' <a href="page-%s.html">اگلا</a>' % pad(i + 1)
        page = (head("صفحہ %d — %s | %s" % (i, title, SITE), "%s — صفحہ %d از %d" % (desc, i, n),
                     "images/page-%s.%s" % (pad(i), ext), rel) +
                '<body class="viewer" data-mode="page" data-issue="%s" data-page="%d">\n'
                '<div id="stage"><div id="book" class="book"><img src="images/page-%s.%s" alt="صفحہ %d"></div></div>\n'
                '<noscript><div class="ns">%s</div></noscript>\n%s</body>\n</html>\n'
                % (esc(slug), i, pad(i), ext, i, nv, SCRIPTS))
        open(os.path.join(d, "page-%s.html" % pad(i)), "w", encoding="utf-8").write(page)


def write_links(issues):
    out = [head("تمام روابط | %s" % SITE, "ہر اشاعت اور ہر صفحے کا لنک").replace("../../", "")]
    out.append('<body class="lib">\n<header class="bar"><a class="brand" href="index.html"><span class="t"><b>تمام روابط</b>'
               '<small>%s</small></span></a><div class="tools"><a class="btn group link" href="index.html">← لائبریری</a></div></header>\n'
               '<main class="wrap links">\n<p style="color:var(--muted);margin-top:24px">ہر لنک کے ساتھ "کاپی" بٹن ہے۔ '
               'یہ صفحہ <code>add_issue.py</code> خود بخود اپ ڈیٹ کرتا ہے۔</p>\n' % SITE)
    for it in issues:
        s, n = it["slug"], it["pages"]
        out.append('<h2>%s <small style="color:var(--muted);font-size:.9rem">(%s)</small></h2>\n' % (esc(it["title"]), esc(it.get("period", ""))))
        out.append('<div class="row"><code>issues/%s/index.html</code><button class="cp" data-h="issues/%s/index.html">کاپی: اشاعت</button>'
                   '<button class="cp" data-h="issues/%s/index.html#1&v=2">کاپی: دو صفحات</button></div>\n' % (s, s, s))
        out.append('<div class="chips">%s</div>\n' % "".join(
            '<a href="issues/%s/page-%s.html" data-h="issues/%s/page-%s.html">%d</a>' % (s, pad(i), s, pad(i), i)
            for i in range(1, n + 1)))
    out.append('</main>\n<script src="assets/js/common.js"></script>\n<script>\n'
               'document.addEventListener("click",function(e){var b=e.target.closest(".cp");if(!b)return;'
               'var u=new URL(b.dataset.h,location.href).href;var t=b.textContent;'
               'var done=function(){b.textContent="کاپی ہو گیا ✓";setTimeout(function(){b.textContent=t},1500)};'
               'if(navigator.clipboard){navigator.clipboard.writeText(u).then(done,function(){prompt("کاپی کریں:",u)})}else{prompt("کاپی کریں:",u)}});\n'
               'document.querySelectorAll(".chips a").forEach(function(a){a.title=new URL(a.dataset.h,location.href).href});\n'
               '</script>\n</body>\n</html>\n')
    open(os.path.join(ROOT, "links.html"), "w", encoding="utf-8").write("".join(out))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="نظام رنگ: نئی اشاعت شامل کریں")
    ap.add_argument("pdf", nargs="?", help="PDF فائل کا راستہ")
    ap.add_argument("--images", help="PDF کی جگہ تصاویر کا فولڈر (ترتیب نام کے مطابق)")
    ap.add_argument("--slug", help="لنک کا نام، مثلاً 2025-02 (انگریزی حروف/اعداد/ڈیش)")
    ap.add_argument("--title", help="اشاعت کا عنوان (اردو)")
    ap.add_argument("--period", default="", help="مثلاً: فروری 2025")
    ap.add_argument("--cover", type=int, default=1, help="سرورق کے طور پر کون سا صفحہ (ڈیفالٹ 1)")
    ap.add_argument("--width", type=int, default=1300, help="صفحے کی تصویر کی چوڑائی پکسل (ڈیفالٹ 1300؛ کم کرنے سے فائلیں ہلکی ہوتی ہیں)")
    ap.add_argument("--format", choices=["webp", "jpg"], help="تصویر کا فارمیٹ (ڈیفالٹ: Pillow ہو تو webp، ورنہ jpg)")
    ap.add_argument("--quality", type=int, help="معیار 1-100 (ڈیفالٹ: webp 70، jpg 78)")
    ap.add_argument("--replace", action="store_true", help="اسی slug کی موجودہ اشاعت بدل دیں")
    ap.add_argument("--rebuild", action="store_true", help="تمام HTML اور روابط کا صفحہ دوبارہ بنائیں")
    ap.add_argument("--remove", metavar="SLUG", help="کوئی اشاعت ہٹائیں")
    a = ap.parse_args()
    issues = load()

    if a.remove:
        issues = [i for i in issues if i["slug"] != a.remove]
        shutil.rmtree(os.path.join(ROOT, "issues", a.remove), ignore_errors=True)
        save(issues); write_links(issues)
        return print("ہٹا دی گئی:", a.remove)

    if a.rebuild:
        for it in issues:
            write_issue_html(it)
        write_links(issues)
        return print("دوبارہ بنایا: %d اشاعتیں" % len(issues))

    if not (a.pdf or a.images) or not a.slug or not a.title:
        ap.error("PDF (یا --images)، --slug اور --title لازمی ہیں")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.slug):
        ap.error("--slug میں صرف چھوٹے انگریزی حروف، اعداد اور ڈیش ہوں")
    exists = [i for i in issues if i["slug"] == a.slug]
    if exists and not a.replace:
        ap.error("یہ slug پہلے سے موجود ہے؛ بدلنے کے لیے --replace لگائیں")

    imgdir = os.path.join(ROOT, "issues", a.slug, "images")
    shutil.rmtree(os.path.join(ROOT, "issues", a.slug), ignore_errors=True)
    os.makedirs(imgdir)

    ext = a.format or ("webp" if can_webp() else "jpg")
    if ext == "webp" and not can_webp():
        sys.exit("webp کے لیے Pillow درکار ہے (pip install pillow)؛ یا --format jpg لگائیں")
    q = a.quality or (70 if ext == "webp" else 78)
    cover = a.cover

    if a.pdf:
        pages, aspect = pdf_meta(a.pdf)
        cover = min(cover, pages)
        print("%s: %d صفحات (%s) ..." % (a.slug, pages, ext), flush=True)
        render_pdf(a.pdf, imgdir, a.width, q, ext, cover)
    else:
        if not can_pil():
            ext = "jpg"
        pages, aspect = render_images(a.images, imgdir, a.width, q, ext, cover)
        cover = min(cover, pages)

    issue = {"slug": a.slug, "title": a.title, "period": a.period, "pages": pages,
             "aspect": round(aspect or 0.707, 4), "cover": cover, "ext": ext}
    if exists:
        issues = [issue if i["slug"] == a.slug else i for i in issues]
    else:
        issues.append(issue)
    save(issues)
    write_issue_html(issue)
    write_links(issues)
    print("مکمل ✓  issues/%s/index.html  (%d صفحات)" % (a.slug, pages))


if __name__ == "__main__":
    main()
