import streamlit as st
import streamlit.components.v1 as components

from datetime import date, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import io
import math


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="시험계획표",
    page_icon="📋",
    layout="wide"
)


# =========================================================
# 색상 / 크기
# =========================================================

TABLE_WIDTH = 770

HEADER_BG = colors.HexColor("#E9EDF2")
GRID_COLOR = colors.HexColor("#BFC5CC")
TEXT_COLOR = colors.HexColor("#222222")

BLUE = colors.HexColor("#4285D4")
ORANGE = colors.HexColor("#F39C12")


# =========================================================
# 한글 폰트
# =========================================================

def register_korean_font():

    font_url = "https://cdn.jsdelivr.net/gh/fonts-archive/NotoSansKR/NotoSansKR-Regular.otf"

    font_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "NotoSansKR-Regular.otf"
    )

    if not os.path.exists(font_path):

        try:
            import urllib.request
            urllib.request.urlretrieve(font_url, font_path)
        except Exception:
            return "Helvetica"

    try:
        pdfmetrics.registerFont(
            TTFont("NotoSansKR", font_path)
        )

        return "NotoSansKR"

    except Exception:
        return "Helvetica"


FONT_NAME = register_korean_font()

st.write("현재 PDF 폰트:", FONT_NAME)


# =========================================================
# PDF 공통 글자 크기
# =========================================================

PDF_BODY_SIZE = 8
PDF_BODY_LEADING = 10


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
    }

    .timeline-title {
        font-size: 21px;
        font-weight: 700;
        margin-top: 30px;
        margin-bottom: 10px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #d0d5db;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 세션 상태
# =========================================================

if "tests" not in st.session_state:
    st.session_state.tests = []


# =========================================================
# 시험 일정 계산
# =========================================================

def calculate_schedule(start_date, tests):

    schedule = []

    current_date = start_date

    for i, test in enumerate(tests):

        period = int(test["period"])

        # 시간 → 일수
        days = max(1, math.ceil(period / 24))

        test_start = current_date
        test_end = test_start + timedelta(days=days - 1)

        schedule.append({
            "no": i + 1,
            "name": test["name"],
            "spec": test["spec"],
            "condition": test["condition"],
            "period": period,
            "start": test_start,
            "end": test_end,
            "remark": test["remark"]
        })

        current_date = test_end + timedelta(days=1)

    return schedule


# =========================================================
# 웹 타임라인
# =========================================================

def make_web_timeline(schedule, result_date):

    if not schedule:
        return ""

    start_date = min(
        x["start"] for x in schedule
    )

    end_date = max(
        max(x["end"] for x in schedule),
        result_date
    )

    total_days = (
        end_date - start_date
    ).days + 1

    left_width = 145
    day_width = 42

    total_width = (
        left_width +
        total_days * day_width
    )

    # 날짜 표시 간격
    if total_days <= 14:
        label_step = 1

    elif total_days <= 31:
        label_step = 3

    elif total_days <= 90:
        label_step = 7

    else:
        label_step = 14

    html = f"""
    <div style="
        width:100%;
        overflow-x:auto;
        overflow-y:hidden;
        border:1px solid #BFC5CC;
        background:white;
        font-family:Arial, sans-serif;
    ">

        <div style="
            min-width:{total_width}px;
        ">

            <!-- 날짜 헤더 -->
            <div style="
                display:flex;
                height:42px;
                background:#E9EDF2;
                border-bottom:1px solid #BFC5CC;
            ">

                <div style="
                    width:{left_width}px;
                    min-width:{left_width}px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-weight:700;
                    border-right:1px solid #BFC5CC;
                    box-sizing:border-box;
                ">
                    시험명
                </div>

                <div style="
                    display:flex;
                    height:42px;
                ">
    """

    for d in range(total_days):

        current = start_date + timedelta(days=d)

        if d % label_step == 0 or current == end_date:
            label = current.strftime("%m/%d")
        else:
            label = ""

        html += f"""
            <div style="
                width:{day_width}px;
                min-width:{day_width}px;
                display:flex;
                align-items:center;
                justify-content:center;
                border-right:1px solid #D5D9DE;
                box-sizing:border-box;
                font-size:13px;
                color:#333;
                font-weight:500;
            ">
                {label}
            </div>
        """

    html += """
                </div>
            </div>
    """

    # =====================================================
    # 시험별 행
    # =====================================================

    for item in schedule:

        html += f"""
        <div style="
            display:flex;
            height:42px;
            border-bottom:1px solid #D5D9DE;
        ">

            <div style="
                width:{left_width}px;
                min-width:{left_width}px;
                display:flex;
                align-items:center;
                justify-content:center;
                border-right:1px solid #BFC5CC;
                box-sizing:border-box;
                font-size:13px;
                font-weight:600;
                background:white;
                padding:4px;
            ">
                {item["name"]}
            </div>

            <div style="
                position:relative;
                height:42px;
                width:{total_days * day_width}px;
                min-width:{total_days * day_width}px;
                background-image:repeating-linear-gradient(
                    to right,
                    transparent 0px,
                    transparent {day_width - 1}px,
                    #E6E9ED {day_width - 1}px,
                    #E6E9ED {day_width}px
                );
            ">
        """

        start_offset = (
            item["start"] - start_date
        ).days

        duration = (
            item["end"] - item["start"]
        ).days + 1

        left = start_offset * day_width
        width = duration * day_width

        # 하나의 연속된 막대
        html += f"""
                <div style="
                    position:absolute;
                    left:{left}px;
                    top:7px;
                    width:{width}px;
                    height:28px;
                    background:#4285D4;
                    border-radius:4px;
                    box-sizing:border-box;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:white;
                    font-size:12px;
                    font-weight:600;
                    overflow:hidden;
                    white-space:nowrap;
                ">
                    {item["period"]} h
                </div>
        """

        html += """
            </div>
        </div>
        """

    # =====================================================
    # 결과 송부
    # =====================================================

    result_offset = (
        result_date - start_date
    ).days

    html += f"""
        <div style="
            display:flex;
            height:42px;
        ">

            <div style="
                width:{left_width}px;
                min-width:{left_width}px;
                display:flex;
                align-items:center;
                justify-content:center;
                border-right:1px solid #BFC5CC;
                box-sizing:border-box;
                font-size:13px;
                font-weight:700;
                background:#FFF8ED;
            ">
                결과 송부
            </div>

            <div style="
                position:relative;
                height:42px;
                width:{total_days * day_width}px;
                min-width:{total_days * day_width}px;
                background-image:repeating-linear-gradient(
                    to right,
                    transparent 0px,
                    transparent {day_width - 1}px,
                    #E6E9ED {day_width - 1}px,
                    #E6E9ED {day_width}px
                );
            ">

                <div style="
                    position:absolute;
                    left:{result_offset * day_width}px;
                    top:7px;
                    width:{day_width}px;
                    height:28px;
                    background:#F39C12;
                    border-radius:4px;
                    box-sizing:border-box;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:white;
                    font-size:11px;
                    font-weight:700;
                ">
                    송부
                </div>

            </div>
        </div>

        </div>
    </div>
    """

    return html


# =========================================================
# PDF Timeline
# =========================================================

def make_pdf_timeline(schedule, result_date):

    start_date = min(
        x["start"] for x in schedule
    )

    end_date = max(
        max(x["end"] for x in schedule),
        result_date
    )

    total_days = (
        end_date - start_date
    ).days + 1

    LEFT_WIDTH = 145
    CHART_WIDTH = TABLE_WIDTH - LEFT_WIDTH

    day_width = (
        CHART_WIDTH / total_days
    )

    # 날짜 표시 간격
    if total_days <= 14:
        label_step = 1

    elif total_days <= 31:
        label_step = 3

    elif total_days <= 90:
        label_step = 7

    else:
        label_step = 14

    # =====================================================
    # Timeline 전용 공통 스타일
    # =====================================================

    timeline_header_style = ParagraphStyle(
        "timeline_header",
        fontName=FONT_NAME,
        fontSize=PDF_BODY_SIZE,
        leading=PDF_BODY_LEADING,
        alignment=TA_CENTER,
        textColor=TEXT_COLOR
    )

    timeline_body_style = ParagraphStyle(
        "timeline_body",
        fontName=FONT_NAME,
        fontSize=PDF_BODY_SIZE,
        leading=PDF_BODY_LEADING,
        alignment=TA_CENTER,
        textColor=TEXT_COLOR
    )

    data = []

    # =====================================================
    # 헤더
    # =====================================================

    header = [
        Paragraph(
            "시험명",
            timeline_header_style
        )
    ]

    for d in range(total_days):

        current = (
            start_date +
            timedelta(days=d)
        )

        if d % label_step == 0 or current == end_date:
            label = current.strftime("%m/%d")
        else:
            label = ""

        header.append(
            Paragraph(
                label,
                timeline_header_style
            )
        )

    data.append(header)

    # =====================================================
    # 시험 행
    # =====================================================

    blue_spans = []

    for row_index, item in enumerate(
        schedule,
        start=1
    ):

        row = [
            Paragraph(
                item["name"],
                timeline_body_style
            )
        ]

        # 날짜 칸 생성
        for d in range(total_days):
            row.append("")

        start_offset = (
            item["start"] -
            start_date
        ).days

        end_offset = (
            item["end"] -
            start_date
        ).days

        # 시험 기간 전체를 하나의 셀로 병합
        blue_spans.append(
            (
                start_offset + 1,
                row_index,
                end_offset + 1,
                row_index
            )
        )

        # 병합 시작 셀에만 시험시간 표시
        row[start_offset + 1] = Paragraph(
            f'{item["period"]} h',
            ParagraphStyle(
                f"timeline_bar_{row_index}",
                fontName=FONT_NAME,
                fontSize=PDF_BODY_SIZE,
                leading=PDF_BODY_LEADING,
                alignment=TA_CENTER,
                textColor=colors.white
            )
        )

        data.append(row)

    # =====================================================
    # 결과 송부 행
    # =====================================================

    result_row = len(data)

    result_row_data = [
        Paragraph(
            "결과 송부",
            timeline_body_style
        )
    ]

    for d in range(total_days):
        result_row_data.append("")

    result_offset = (
        result_date - start_date
    ).days

    result_row_data[result_offset + 1] = Paragraph(
        "송부",
        ParagraphStyle(
            "result_bar",
            fontName=FONT_NAME,
            fontSize=PDF_BODY_SIZE,
            leading=PDF_BODY_LEADING,
            alignment=TA_CENTER,
            textColor=colors.white
        )
    )

    data.append(result_row_data)

    # =====================================================
    # 테이블
    # =====================================================

    table = Table(
        data,
        colWidths=[
            LEFT_WIDTH
        ] + [
            day_width
        ] * total_days,
        rowHeights=[
            30
        ] + [
            30
        ] * len(schedule) + [
            30
        ],
        repeatRows=1
    )

    style_commands = [

        # 전체 외곽선
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.6,
            GRID_COLOR
        ),

        # 전체 기본 격자
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            GRID_COLOR
        ),

        # 헤더 배경
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            HEADER_BG
        ),

        # 수직 중앙
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

        # 전체 중앙
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER"
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            1
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            1
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            1
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            1
        ),

        # 결과 송부 이름
        (
            "BACKGROUND",
            (0, result_row),
            (0, result_row),
            colors.HexColor("#FFF8ED")
        ),
    ]

    # =====================================================
    # 시험 막대 병합 + 파란색
    # =====================================================

    for start_col, row, end_col, _ in blue_spans:

        # 셀 병합
        style_commands.append(
            (
                "SPAN",
                (start_col, row),
                (end_col, row)
            )
        )

        # 하나의 연속된 파란색 막대
        style_commands.append(
            (
                "BACKGROUND",
                (start_col, row),
                (end_col, row),
                BLUE
            )
        )

        # 병합된 막대 외곽선 제거
        style_commands.append(
            (
                "BOX",
                (start_col, row),
                (end_col, row),
                0,
                BLUE
            )
        )

    # =====================================================
    # 결과 송부 주황색
    # =====================================================

    style_commands.append(
        (
            "BACKGROUND",
            (
                result_offset + 1,
                result_row
            ),
            (
                result_offset + 1,
                result_row
            ),
            ORANGE
        )
    )

    table.setStyle(
        TableStyle(style_commands)
    )

    return table


# =========================================================
# PDF 생성
# =========================================================

def make_pdf(
    customer,
    project,
    manager,
    start_date,
    result_date,
    special_note,
    schedule
):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    # =====================================================
    # PDF 공통 스타일
    # =====================================================

    title_style = ParagraphStyle(
        "title",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=TEXT_COLOR,
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        "section",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        textColor=TEXT_COLOR,
        spaceBefore=5,
        spaceAfter=5
    )

    # -----------------------------------------------------
    # Project Information 내용
    # -----------------------------------------------------

    project_body_style = ParagraphStyle(
        "project_body",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=PDF_BODY_SIZE,
        leading=PDF_BODY_LEADING,
        alignment=TA_LEFT,
        textColor=TEXT_COLOR
    )

    # -----------------------------------------------------
    # Test Schedule 내용
    # -----------------------------------------------------

    schedule_body_style = ParagraphStyle(
        "schedule_body",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=PDF_BODY_SIZE,
        leading=PDF_BODY_LEADING,
        alignment=TA_CENTER,
        textColor=TEXT_COLOR
    )

    # -----------------------------------------------------
    # 공통 헤더
    # -----------------------------------------------------

    header_style = ParagraphStyle(
        "header",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=PDF_BODY_SIZE,
        leading=PDF_BODY_LEADING,
        alignment=TA_CENTER,
        textColor=TEXT_COLOR
    )

    story = []

    # =====================================================
    # 제목
    # =====================================================

    story.append(
        Paragraph(
            "시험계획표",
            title_style
        )
    )

    # =====================================================
    # PROJECT INFORMATION
    # =====================================================

    story.append(
        Paragraph(
            "PROJECT INFORMATION",
            section_style
        )
    )

    project_data = [
        [
            Paragraph(
                "고객사",
                header_style
            ),
            Paragraph(
                customer,
                project_body_style
            ),
            Paragraph(
                "Project",
                header_style
            ),
            Paragraph(
                project,
                project_body_style
            )
        ],

        [
            Paragraph(
                "담당자",
                header_style
            ),
            Paragraph(
                manager,
                project_body_style
            ),
            Paragraph(
                "시험 시작일",
                header_style
            ),
            Paragraph(
                start_date.strftime("%Y-%m-%d"),
                project_body_style
            )
        ],

        [
            Paragraph(
                "최종 결과 송부일",
                header_style
            ),
            Paragraph(
                result_date.strftime("%Y-%m-%d"),
                project_body_style
            ),
            Paragraph(
                "특이사항",
                header_style
            ),
            Paragraph(
                special_note,
                project_body_style
            )
        ]
    ]

    project_table = Table(
        project_data,
        colWidths=[
            90,
            190,
            110,
            380
        ],
        rowHeights=[
            25,
            25,
            25
        ]
    )

    project_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                HEADER_BG
            ),

            (
                "BACKGROUND",
                (2, 0),
                (2, -1),
                HEADER_BG
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                GRID_COLOR
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                GRID_COLOR
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    story.append(project_table)

    story.append(
        Spacer(1, 10)
    )

    # =====================================================
    # TEST SCHEDULE
    # =====================================================

    story.append(
        Paragraph(
            "TEST SCHEDULE",
            section_style
        )
    )

    schedule_data = []

    schedule_data.append([
        Paragraph("No.", header_style),
        Paragraph("시험명", header_style),
        Paragraph("시험규격", header_style),
        Paragraph("시험조건", header_style),
        Paragraph("기간(h)", header_style),
        Paragraph("시작일", header_style),
        Paragraph("종료일", header_style),
        Paragraph("비고", header_style)
    ])

    for item in schedule:

        schedule_data.append([

            Paragraph(
                str(item["no"]),
                schedule_body_style
            ),

            Paragraph(
                item["name"],
                schedule_body_style
            ),

            Paragraph(
                item["spec"],
                schedule_body_style
            ),

            Paragraph(
                item["condition"],
                schedule_body_style
            ),

            Paragraph(
                str(item["period"]),
                schedule_body_style
            ),

            Paragraph(
                item["start"].strftime("%Y-%m-%d"),
                schedule_body_style
            ),

            Paragraph(
                item["end"].strftime("%Y-%m-%d"),
                schedule_body_style
            ),

            Paragraph(
                item["remark"],
                schedule_body_style
            )
        ])

    schedule_table = Table(
        schedule_data,
        colWidths=[
            35,
            115,
            100,
            145,
            65,
            80,
            80,
            150
        ],
        repeatRows=1
    )

    schedule_table.setStyle(
        TableStyle([

            # 헤더 배경
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                HEADER_BG
            ),

            # 외곽선
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                GRID_COLOR
            ),

            # 내부선
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                GRID_COLOR
            ),

            # 세로 중앙
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            # 테이블 중앙
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    story.append(schedule_table)

    story.append(
        Spacer(1, 10)
    )

    # =====================================================
    # TEST TIMELINE
    # =====================================================

    story.append(
        Paragraph(
            "TEST TIMELINE",
            section_style
        )
    )

    timeline_table = make_pdf_timeline(
        schedule,
        result_date
    )

    story.append(
        timeline_table
    )

    # =====================================================
    # PDF 생성
    # =====================================================

    doc.build(story)

    buffer.seek(0)

    return buffer


# =========================================================
# 메인 화면
# =========================================================

st.markdown(
    '<div class="main-title">📋 시험계획표</div>',
    unsafe_allow_html=True
)


# =========================================================
# PROJECT INFORMATION
# =========================================================

st.markdown(
    '<div class="section-title">PROJECT INFORMATION</div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:

    customer = st.text_input(
        "고객사",
        placeholder="고객사명을 입력하세요"
    )

with col2:

    project = st.text_input(
        "Project",
        placeholder="Project명을 입력하세요"
    )

with col3:

    manager = st.text_input(
        "담당자",
        placeholder="담당자를 입력하세요"
    )


col4, col5 = st.columns(2)

with col4:

    start_date = st.date_input(
        "시험 시작일",
        value=date.today()
    )

with col5:

    result_date = st.date_input(
        "최종 결과 송부일",
        value=date.today()
    )


special_note = st.text_area(
    "특이사항",
    placeholder="특이사항을 입력하세요",
    height=80
)


# =========================================================
# TEST ITEMS
# =========================================================

st.markdown(
    '<div class="section-title">TEST ITEMS</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns([1.2, 1])

with c1:

    test_name = st.text_input(
        "시험명",
        placeholder="예: 인장강도"
    )

with c2:

    test_spec = st.text_input(
        "시험규격",
        placeholder="예: ASTM D412"
    )


c3, c4 = st.columns([1.2, 0.8])

with c3:

    test_condition = st.text_input(
        "시험조건",
        placeholder="예: 23℃ × 72h"
    )

with c4:

    test_period = st.number_input(
        "시험 기간(시간)",
        min_value=1,
        value=24,
        step=1,
        format="%d"
    )


test_remark = st.text_input(
    "비고",
    placeholder="비고"
)


if st.button(
    "➕ 시험 추가",
    use_container_width=True
):

    if not test_name.strip():

        st.warning(
            "시험명을 입력해주세요."
        )

    else:

        st.session_state.tests.append({

            "name": test_name,

            "spec": test_spec,

            "condition": test_condition,

            "period": int(test_period),

            "remark": test_remark

        })

        st.rerun()


# =========================================================
# TEST LIST
# =========================================================

if st.session_state.tests:

    st.markdown(
        '<div class="section-title">TEST LIST</div>',
        unsafe_allow_html=True
    )

    schedule = calculate_schedule(
        start_date,
        st.session_state.tests
    )

    # 헤더
    h1, h2, h3, h4, h5, h6, h7 = st.columns(
        [
            0.4,
            1.8,
            1.5,
            1.5,
            0.8,
            1.4,
            0.5
        ]
    )

    h1.markdown("**No.**")
    h2.markdown("**시험명**")
    h3.markdown("**시험규격**")
    h4.markdown("**시험조건**")
    h5.markdown("**기간(h)**")
    h6.markdown("**일정**")
    h7.markdown("**삭제**")

    for i, item in enumerate(schedule):

        c1, c2, c3, c4, c5, c6, c7 = st.columns(
            [
                0.4,
                1.8,
                1.5,
                1.5,
                0.8,
                1.4,
                0.5
            ]
        )

        c1.write(
            item["no"]
        )

        c2.write(
            item["name"]
        )

        c3.write(
            item["spec"]
        )

        c4.write(
            item["condition"]
        )

        c5.write(
            item["period"]
        )

        c6.caption(
            f'{item["start"].strftime("%Y-%m-%d")} ~ '
            f'{item["end"].strftime("%Y-%m-%d")}'
        )

        if c7.button(
            "🗑️",
            key=f"delete_{i}"
        ):

            st.session_state.tests.pop(i)

            st.rerun()


# =========================================================
# TEST TIMELINE
# =========================================================

if st.session_state.tests:

    schedule = calculate_schedule(
        start_date,
        st.session_state.tests
    )

    st.markdown(
        '<div class="timeline-title">TEST TIMELINE</div>',
        unsafe_allow_html=True
    )

    timeline_html = make_web_timeline(
        schedule,
        result_date
    )

    components.html(
        timeline_html,
        height=250,
        scrolling=True
    )


# =========================================================
# PDF DOWNLOAD
# =========================================================

if st.session_state.tests:

    schedule = calculate_schedule(
        start_date,
        st.session_state.tests
    )

    pdf_file = make_pdf(
        customer=customer,
        project=project,
        manager=manager,
        start_date=start_date,
        result_date=result_date,
        special_note=special_note,
        schedule=schedule
    )

    st.markdown("")

    st.download_button(
        label="📄 PDF 다운로드",
        data=pdf_file,
        file_name="시험계획표.pdf",
        mime="application/pdf",
        use_container_width=True
    )
