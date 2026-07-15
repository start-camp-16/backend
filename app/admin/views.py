from html import escape
from json import dumps
from urllib.parse import urlencode

from app.admin.courses import CourseListPage
from app.models import Course


def _url(page: int, query: str) -> str:
    params: dict[str, str | int] = {"page": page}
    if query:
        params["q"] = query
    return f"/admin/courses?{urlencode(params)}"


def _course_card(course: Course, page: CourseListPage) -> str:
    title = escape(course.title, quote=True)
    confirmation = escape(
        dumps(f"{course.title} 코스를 삭제할까요?", ensure_ascii=False),
        quote=True,
    )
    delete_query = urlencode({"page": page.page, "q": page.query})
    stops = "".join(
        (
            '<li class="stop">'
            f'<span class="stop-index">{stop.position}</span>'
            f'<span class="stop-title">{escape(stop.location.title, quote=True)}</span>'
            "</li>"
        )
        for stop in sorted(course.stops, key=lambda item: item.position)
    )
    public_id = escape(course.public_id, quote=True)
    return f"""
      <article class="course-card">
        <div class="course-heading">
          <div class="course-title-block">
            <p class="eyebrow">저장 코스</p>
            <h2>{title}</h2>
            <p class="public-id">{public_id}</p>
          </div>
          <form method="post"
                action="/admin/courses/{public_id}/delete?{escape(delete_query, quote=True)}"
                onsubmit="return confirm({confirmation})">
            <button class="delete" type="submit">강제 삭제</button>
          </form>
        </div>
        <dl class="course-meta">
          <div><dt>생성</dt><dd>{course.created_at:%Y-%m-%d %H:%M} UTC</dd></div>
          <div><dt>수정</dt><dd>{course.updated_at:%Y-%m-%d %H:%M} UTC</dd></div>
          <div><dt>장소</dt><dd>{len(course.stops)}곳</dd></div>
        </dl>
        <ol class="stops" aria-label="방문 장소 순서">{stops}</ol>
      </article>
    """


def _pagination(page: CourseListPage) -> str:
    previous = (
        f'<a href="{escape(_url(page.page - 1, page.query), quote=True)}">이전</a>'
        if page.page > 1
        else '<span class="disabled">이전</span>'
    )
    following = (
        f'<a href="{escape(_url(page.page + 1, page.query), quote=True)}">다음</a>'
        if page.page < page.total_pages
        else '<span class="disabled">다음</span>'
    )
    return (
        '<nav class="pagination" aria-label="페이지 이동">'
        f"{previous}"
        f'<strong>{page.page} / {page.total_pages} 페이지</strong>'
        f"{following}"
        "</nav>"
    )


def render_course_list(page: CourseListPage) -> str:
    cards = "".join(_course_card(course, page) for course in page.items)
    if not cards:
        cards = (
            '<section class="empty">'
            '<p class="eyebrow">검색 결과 0개</p>'
            "<h2>검색 결과가 없습니다</h2>"
            "<p>다른 제목으로 검색하거나 검색어를 지워 주세요.</p>"
            "</section>"
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>저장된 코스 · 뭐할구 관리자</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #15211b;
      --muted: #637068;
      --line: #d8e2dc;
      --mist: #eef3f0;
      --paper: #f8faf9;
      --card: #ffffff;
      --route: #0e6b5c;
      --route-soft: #d8eee5;
      --danger: #b42318;
      --danger-soft: #fff1ef;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
    }}
    main {{ width: min(960px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 64px; }}
    .page-header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 26px;
    }}
    h1 {{ margin: 2px 0 0; font-size: clamp(34px, 6vw, 56px); letter-spacing: -.055em; }}
    h2 {{ margin: 0; font-size: 21px; letter-spacing: -.025em; }}
    .eyebrow {{
      margin: 0 0 5px;
      color: var(--route);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .count {{ margin: 0; color: var(--muted); font-size: 14px; }}
    .search {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 9px;
      padding: 8px;
      margin-bottom: 22px;
      background: var(--mist);
      border-radius: 15px;
    }}
    input {{
      min-width: 0;
      border: 1px solid transparent;
      border-radius: 10px;
      background: var(--card);
      padding: 12px 14px;
      color: var(--ink);
      font: inherit;
    }}
    button, a {{ font: inherit; }}
    .search button, .pagination a {{
      border: 0;
      border-radius: 10px;
      background: var(--route);
      color: white;
      padding: 12px 18px;
      text-decoration: none;
    }}
    .course-card {{
      position: relative;
      overflow: hidden;
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: 17px;
      background: var(--card);
      padding: 23px;
    }}
    .course-card::before {{
      position: absolute;
      inset: 0 auto 0 0;
      width: 5px;
      background: var(--route);
      content: "";
    }}
    .course-heading {{
      display: flex;
      justify-content: space-between;
      align-items: start;
      gap: 20px;
    }}
    .public-id {{
      margin: 7px 0 0;
      overflow-wrap: anywhere;
      color: var(--muted);
      font: 12px ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .delete {{
      border: 1px solid #edb8b3;
      border-radius: 9px;
      background: var(--danger-soft);
      color: var(--danger);
      padding: 9px 12px;
      cursor: pointer;
      font-weight: 700;
    }}
    .course-meta {{ display: flex; gap: 22px; margin: 22px 0; }}
    .course-meta div {{ display: flex; gap: 7px; }}
    dt, dd {{ margin: 0; font-size: 13px; }}
    dt {{ color: var(--muted); }}
    .stops {{
      position: relative;
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}
    .stops::before {{
      position: absolute;
      top: 12px;
      bottom: 12px;
      left: 12px;
      width: 2px;
      background: var(--route-soft);
      content: "";
    }}
    .stop {{ position: relative; display: flex; align-items: center; gap: 11px; }}
    .stop-index {{
      z-index: 1;
      display: grid;
      place-items: center;
      width: 26px;
      height: 26px;
      border: 2px solid var(--route-soft);
      border-radius: 50%;
      background: var(--card);
      color: var(--route);
      font-size: 11px;
      font-weight: 800;
    }}
    .stop-title {{ font-size: 14px; }}
    .empty {{
      border: 1px dashed #b8c7bf;
      border-radius: 17px;
      padding: 64px 20px;
      text-align: center;
    }}
    .empty p:last-child {{ margin-bottom: 0; color: var(--muted); }}
    .pagination {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 14px;
      margin-top: 28px;
    }}
    .pagination strong {{ font-size: 13px; }}
    .pagination .disabled {{ color: #99a49e; padding: 12px 18px; }}
    :focus-visible {{ outline: 3px solid #71c4a5; outline-offset: 2px; }}
    @media (max-width: 640px) {{
      main {{ width: min(100% - 20px, 960px); padding-top: 28px; }}
      .page-header, .course-heading {{ align-items: stretch; flex-direction: column; }}
      .course-meta {{ flex-direction: column; gap: 6px; }}
      .delete {{ width: 100%; }}
      .pagination {{ gap: 5px; }}
      .pagination a, .pagination .disabled {{ padding: 10px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="page-header">
      <div><p class="eyebrow">뭐할구 관리자</p><h1>저장된 코스</h1></div>
      <p class="count">{page.total_items}개 코스</p>
    </header>
    <form class="search" method="get" action="/admin/courses">
      <input type="search" name="q" value="{escape(page.query, quote=True)}"
             placeholder="코스 제목 검색" aria-label="코스 제목 검색">
      <button type="submit">검색</button>
    </form>
    <section aria-live="polite">{cards}</section>
    {_pagination(page)}
  </main>
</body>
</html>"""
