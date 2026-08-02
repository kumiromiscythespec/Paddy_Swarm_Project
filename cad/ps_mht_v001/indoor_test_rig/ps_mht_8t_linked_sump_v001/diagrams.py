"""Japanese SVG diagrams for the Phase 4T-LS-A reference architecture."""

from __future__ import annotations

from html import escape
from pathlib import Path


Node = tuple[float, float, float, float, str, str]
Edge = tuple[float, float, float, float, str, str, bool]


def _render_svg(
    title: str,
    subtitle: str,
    nodes: list[Node],
    edges: list[Edge],
    notes: list[str],
) -> str:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">',
        '<path d="M0,0 L10,4 L0,8 Z" fill="context-stroke"/>',
        "</marker>",
        '<style>text{font-family:"Yu Gothic","Noto Sans CJK JP",sans-serif;fill:#17212b}.title{font-size:28px;font-weight:700}.sub{font-size:16px;fill:#455a64}.node{stroke:#263238;stroke-width:2}.label{font-size:17px;font-weight:600;text-anchor:middle}.edge{fill:none;stroke-width:4;marker-end:url(#arrow)}.edge-label{font-size:14px;text-anchor:middle}.note{font-size:15px}</style>',
        "</defs>",
        '<rect width="1200" height="700" fill="#f7fafc"/>',
        f'<text x="50" y="48" class="title">{escape(title)}</text>',
        f'<text x="50" y="78" class="sub">{escape(subtitle)}</text>',
    ]
    for x1, y1, x2, y2, label, color, dashed in edges:
        dash = ' stroke-dasharray="10 8"' if dashed else ""
        parts.append(
            f'<path d="M{x1},{y1} L{x2},{y2}" class="edge" stroke="{color}"{dash}/>'
        )
        if label:
            parts.append(
                f'<text x="{0.5 * (x1 + x2):g}" y="{0.5 * (y1 + y2) - 8:g}" '
                f'class="edge-label">{escape(label)}</text>'
            )
    for x, y, width, height, label, color in nodes:
        parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="12" '
            f'class="node" fill="{color}"/>'
        )
        lines = label.split("|")
        start_y = y + 0.5 * height - 10.0 * (len(lines) - 1)
        parts.append(f'<text x="{x + 0.5 * width:g}" y="{start_y:g}" class="label">')
        for index, line in enumerate(lines):
            dy = "0" if index == 0 else "22"
            parts.append(
                f'<tspan x="{x + 0.5 * width:g}" dy="{dy}">{escape(line)}</tspan>'
            )
        parts.append("</text>")
    note_y = 610
    for note in notes:
        parts.append(f'<text x="50" y="{note_y}" class="note">• {escape(note)}</text>')
        note_y += 24
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def diagram_definitions() -> dict[str, str]:
    blue = "#d8ecff"
    green = "#dcf5e6"
    amber = "#fff0c7"
    red = "#ffdcdc"
    gray = "#e9eef2"
    water = "#1976d2"
    safety = "#d84315"
    return {
        "daytime_water_path_phase4tlsa.svg": _render_svg(
            "昼間の養液循環経路",
            "最大8タワーを1台のポンプで並列給水・並列均水するREFERENCE",
            [
                (50, 220, 170, 90, "共通ポンプ槽", blue),
                (280, 220, 160, 90, "循環ポンプ|DC12V 20W", amber),
                (500, 110, 190, 80, "安全バイパス|常時逃がし", green),
                (500, 280, 190, 90, "上部8分岐|マニホールド", blue),
                (760, 280, 170, 90, "タワーA～H|開放吐出", green),
                (990, 280, 160, 90, "ローカル|サンプA～H", blue),
                (760, 450, 190, 80, "個別均水弁|A～H", amber),
                (480, 450, 210, 80, "共通均水主管|並列", blue),
            ],
            [
                (220, 265, 280, 265, "吸込", water, False),
                (440, 250, 500, 150, "バイパス", water, False),
                (440, 280, 500, 325, "吐出", water, False),
                (690, 325, 760, 325, "8枝", water, False),
                (930, 325, 990, 325, "重力流下", water, False),
                (1070, 370, 855, 450, "均水", water, False),
                (760, 490, 690, 490, "", water, False),
                (480, 490, 135, 310, "中央へ戻る", water, False),
                (595, 190, 135, 220, "槽へ戻す", water, False),
            ],
            ["サンプ間の直列デイジーチェーンは禁止", "8枝すべて閉鎖時もポンプ出口を完全閉止しない"],
        ),
        "nighttime_water_path_phase4tlsa.svg": _render_svg(
            "夜間の水路状態",
            "上部10L清水槽と養液循環ゾーンを分離する",
            [
                (90, 160, 210, 100, "上部10L|清水一時タンク", blue),
                (410, 160, 180, 100, "清水→タワー弁|CLOSED", red),
                (720, 160, 210, 100, "タワー上部|清水供給なし", gray),
                (90, 390, 200, 90, "ローカルサンプ", blue),
                (400, 390, 200, 90, "共通ポンプ槽", blue),
                (720, 390, 210, 90, "養液循環|設定に従う", green),
            ],
            [
                (300, 210, 410, 210, "閉鎖", safety, True),
                (590, 210, 720, 210, "流れなし", safety, True),
                (290, 435, 400, 435, "均水", water, False),
                (600, 435, 720, 435, "循環系のみ", water, False),
            ],
            ["清水槽には夜間も清水だけを保持", "清水補給設備の電力は循環ポンプWhへ含めない"],
        ),
        "parallel_sumps_4tower_phase4tlsa.svg": _render_svg(
            "4タワー室内試験：8枝主管の4枝使用",
            "床寸法はMEASUREMENT_PENDING。配置は寸法確定ではない",
            [
                *[(80 + 250 * i, 170, 170, 100, f"タワー{letter}|サンプ{letter}", green) for i, letter in enumerate("ABCD")],
                (100, 390, 920, 80, "背面共通均水主管 32～40mm ID REFERENCE", blue),
                (500, 510, 200, 80, "中央ポンプ槽", blue),
                (80, 510, 300, 70, "未使用枝 E～H|個別閉鎖", gray),
            ],
            [
                *[(165 + 250 * i, 270, 165 + 250 * i, 390, "個別弁", water, False) for i in range(4)],
                (560, 470, 600, 510, "中央接続", water, False),
            ],
            ["通路幅600mm以上、推奨700～800mm", "主管・安全樋は背面サービス経路に置く"],
        ),
        "parallel_sumps_8tower_expansion_phase4tlsa.svg": _render_svg(
            "8タワー拡張REFERENCE",
            "A～D使用、E～H閉鎖状態から段階的に4→6→8へ拡張",
            [
                *[(55 + 140 * i, 155, 120, 90, f"{letter}|{'使用' if i < 4 else '閉鎖'}", green if i < 4 else gray) for i, letter in enumerate("ABCDEFGH")],
                (70, 360, 1060, 80, "共通均水主管：全枝が独立した並列接続", blue),
                (500, 500, 200, 80, "中央ポンプ槽", blue),
            ],
            [
                *[(115 + 140 * i, 245, 115 + 140 * i, 360, "弁", water if i < 4 else "#78909c", i >= 4) for i in range(8)],
                (600, 440, 600, 500, "", water, False),
            ],
            ["8タワー能力は公称700L/hだけでは未合格", "6・8タワーは実揚程下の枝流量試験後に使用"],
        ),
        "individual_isolation_phase4tlsa.svg": _render_svg(
            "個別隔離手順",
            "上部給水を止めて排水完了後に均水弁を閉じる",
            [
                (70, 230, 180, 90, "上部給水弁|1 閉鎖", red),
                (320, 230, 180, 90, "タワー|2 排水待ち", green),
                (570, 230, 180, 90, "ローカルサンプ|3 水位安定確認", blue),
                (820, 230, 180, 90, "均水弁|4 ゆっくり閉鎖", amber),
                (820, 410, 180, 90, "整備・切離し|5", gray),
            ],
            [
                (250, 275, 320, 275, "", safety, False),
                (500, 275, 570, 275, "", safety, False),
                (750, 275, 820, 275, "", safety, False),
                (910, 320, 910, 410, "", safety, False),
            ],
            ["均水弁を先に閉じたまま給水継続は禁止", "再接続前に清掃、EC/pH、水位整合、漏れ確認を行う"],
        ),
        "emergency_overflow_phase4tlsa.svg": _render_svg(
            "非常オーバーフロー",
            "隔離状態を循環系へ再接続しない独立安全経路",
            [
                (90, 220, 220, 100, "ローカルサンプ|HIGH出口 25～32mm", blue),
                (420, 220, 240, 100, "通常乾燥の|共通安全樋", amber),
                (790, 220, 250, 100, "非循環式|非常受け槽", red),
                (420, 430, 240, 80, "共通均水主管|接続禁止", gray),
            ],
            [
                (310, 270, 420, 270, "異常流", safety, False),
                (660, 270, 790, 270, "目視可能", safety, False),
                (540, 320, 540, 430, "戻さない", safety, True),
            ],
            ["病害・清掃中の液を循環へ戻さない", "受け槽容量は枝流量×検知時間＋余裕で決める"],
        ),
        "room_height_section_phase4tlsa.svg": _render_svg(
            "室内高さ断面REFERENCE",
            "天井2300mm確定。床の縦横寸法は未測定",
            [
                (60, 100, 1080, 30, "天井 2300mm", gray),
                (170, 190, 260, 100, "上部10L清水槽|上端≤2050mm", blue),
                (170, 330, 260, 70, "独立棚|推奨1700mm", amber),
                (650, 250, 220, 260, "5段タワー|荷重は乾式架台へ", green),
                (620, 540, 280, 50, "低背サンプ・乾式デッキ", blue),
            ],
            [
                (300, 130, 300, 190, "天井余裕≥250mm", safety, False),
                (760, 510, 760, 540, "", water, False),
            ],
            ["清水槽重量をタワーへ載せない", "正確な平面配置はroom length/width実測後"],
        ),
        "rear_trunk_service_route_phase4tlsa.svg": _render_svg(
            "背面主管サービス経路",
            "通路を横断せず、弁操作面とサンプ引出しを通路側へ統一",
            [
                (80, 140, 950, 90, "壁際：非常安全樋（通常乾燥）", amber),
                (80, 280, 950, 90, "保護された共通均水主管・清掃口・低点排水", blue),
                (80, 430, 210, 90, "タワー・サンプ", green),
                (350, 430, 210, 90, "タワー・サンプ", green),
                (620, 430, 210, 90, "タワー・サンプ", green),
                (900, 430, 210, 90, "タワー・サンプ", green),
                (80, 570, 1030, 60, "人通路 ≥600mm（推奨700～800mm）", gray),
            ],
            [
                (185, 430, 185, 370, "背面枝", water, False),
                (455, 430, 455, 370, "", water, False),
                (725, 430, 725, 370, "", water, False),
                (1005, 430, 1005, 370, "", water, False),
            ],
            ["配管を足で踏める位置へ露出しない", "水配管と電気配線を分離する"],
        ),
        "circulation_pump_power_meter_wiring_phase4tlsa.svg": _render_svg(
            "循環ポンプ専用Wh測定配線",
            "測定名：CIRCULATION_PUMP_ONLY_Wh",
            [
                (70, 240, 170, 90, "12V電源", gray),
                (300, 240, 170, 90, "主ヒューズ", red),
                (530, 240, 200, 90, "DC積算電力計|V / A / W / Wh", amber),
                (790, 240, 170, 90, "タイマー|またはスイッチ", gray),
                (1020, 240, 140, 90, "循環ポンプ", blue),
                (530, 440, 200, 80, "清水補給設備|別測定", green),
            ],
            [
                (240, 285, 300, 285, "", "#455a64", False),
                (470, 285, 530, 285, "", "#455a64", False),
                (730, 285, 790, 285, "", "#455a64", False),
                (960, 285, 1020, 285, "", "#455a64", False),
                (630, 330, 630, 440, "含めない", safety, True),
            ],
            ["センサーとタイマー待機電力も別項目", "4/6/8タワー別Wh、1塔・1L当たりWhを算出"],
        ),
    }


def write_phase4tlsa_diagrams(output_directory: Path) -> list[Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, content in diagram_definitions().items():
        path = output_directory / name
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths
