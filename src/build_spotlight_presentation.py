"""
Generator script for HSL_Bike_Heatmap_Presentation_Spotlight.pptx.
Builds a publication-quality, 6-slide, 3-minute Spotlight presentation
tailored for city-bike operators and HSL transport planners, adhering to
UH-CS Introduction to Data Science mini-project presentation guidelines.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

# Color Palette Constants
COLOR_DARK_BG = "12313A"      # Slate Teal (Slide 1 background)
COLOR_LIGHT_BG = "F7FAFA"     # Off-White / Soft Ice (Slides 2-6 background)
COLOR_CARD_BG = "FFFFFF"      # Pure white card background
COLOR_CARD_BORDER = "DCE6E8"  # Subtle grey-teal border
COLOR_PRIMARY_DARK = RGBColor(0x12, 0x31, 0x3A)  # Main text / titles on light
COLOR_PRIMARY_LIGHT = RGBColor(0xFF, 0xFF, 0xFF) # Main text on dark
COLOR_TEAL_ACCENT = RGBColor(0x00, 0x7E, 0x87)   # Primary brand accent
COLOR_MUTED_SLATE = RGBColor(0x54, 0x70, 0x78)   # Secondary / subtext
COLOR_LIGHT_ACCENT = RGBColor(0xA6, 0xDC, 0xDD)  # Accent on dark
COLOR_LIGHT_MUTED = RGBColor(0xC8, 0xDB, 0xDD)   # Secondary text on dark
COLOR_CORAL_ACCENT = RGBColor(0xD4, 0x5C, 0x39)  # Deficit / alert highlight
COLOR_BLUE_ACCENT = RGBColor(0x2B, 0x5C, 0x8F)   # Surplus / secondary highlight

FONT_HEADING = "Aptos"
FONT_BODY = "Aptos"


def set_slide_background(slide, color_hex):
    """Sets solid background color via DrawingML XML."""
    bg_xml = f"""
    <p:bg xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
      <p:bgPr>
        <a:solidFill>
          <a:srgbClr val="{color_hex}"/>
        </a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    """
    cSld = slide._element.cSld
    for b in cSld.xpath("p:bg"):
        cSld.remove(b)
    cSld.insert(0, parse_xml(bg_xml))


def add_slide_header(slide, slide_num, category, title, subtitle, is_dark=False):
    """Adds a standardized top header banner and bottom-right page indicator."""
    # Category badge
    tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(10.5), Inches(0.3))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = f"{slide_num:02d} | {category.upper()}"
    p_cat.font.name = FONT_HEADING
    p_cat.font.size = Pt(11)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_LIGHT_ACCENT if is_dark else COLOR_TEAL_ACCENT

    # Main Headline (Assertion / Takeaway)
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.68), Inches(11.0), Inches(0.55))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(23)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_PRIMARY_LIGHT if is_dark else COLOR_PRIMARY_DARK

    # Subtitle / Empirical Scope
    tb_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.24), Inches(11.0), Inches(0.38))
    tf_sub = tb_sub.text_frame
    tf_sub.word_wrap = True
    tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = subtitle
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(12.5)
    p_sub.font.color.rgb = COLOR_LIGHT_MUTED if is_dark else COLOR_MUTED_SLATE

    # Page indicator (bottom right)
    tb_num = slide.shapes.add_textbox(Inches(11.5), Inches(6.9), Inches(1.0), Inches(0.3))
    tf_num = tb_num.text_frame
    tf_num.margin_left = tf_num.margin_right = tf_num.margin_top = tf_num.margin_bottom = 0
    p_num = tf_num.paragraphs[0]
    p_num.alignment = PP_ALIGN.RIGHT
    p_num.text = f"{slide_num:02d} / 06"
    p_num.font.name = FONT_BODY
    p_num.font.size = Pt(11)
    p_num.font.bold = True
    p_num.font.color.rgb = RGBColor(0x9C, 0xBA, 0xBC) if is_dark else COLOR_MUTED_SLATE


def add_card(slide, left, top, width, height, bg_hex="FFFFFF", border_hex="DCE6E8"):
    """Adds a rounded rectangle container card."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    r = int(bg_hex[0:2], 16)
    g = int(bg_hex[2:4], 16)
    b = int(bg_hex[4:6], 16)
    shape.fill.fore_color.rgb = RGBColor(r, g, b)
    if border_hex:
        shape.line.color.rgb = RGBColor(int(border_hex[0:2], 16), int(border_hex[2:4], 16), int(border_hex[4:6], 16))
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def set_speaker_notes(slide, timing, duration, notes_text):
    """Sets structured speaker notes on slide with auto-computed word count."""
    wc = len(notes_text.strip().split())
    formatted_notes = f"Timing: {timing} | Duration: {duration} | Word Count: {wc} words\n\n{notes_text.strip()}"
    slide.notes_slide.notes_text_frame.text = formatted_notes


def build_spotlight_presentation(base_pptx_path, out_pptx_path):
    prs = Presentation(base_pptx_path)

    # Remove existing slides cleanly from rels and list
    for sldId in list(prs.slides._sldIdLst):
        rId = sldId.rId
        prs.slides._sldIdLst.remove(sldId)
        prs.part.drop_rel(rId)

    blank_layout = prs.slide_layouts[5]
    fig_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "figures")

    # =========================================================================
    # SLIDE 1: Title & The Rebalancing Challenge (Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_DARK_BG)
    add_slide_header(s1, 1, "Operational Challenge", "Anticipating Urban Bike Depletion & Dock Congestion",
                     "HSL City-Bike Rebalancing Insights Across 457 Stations & 4.98 Million Trips (2024–2025)", is_dark=True)

    # Center Hero Card
    card_w = Inches(11.73)
    card_h = Inches(3.6)
    card_y = Inches(1.9)
    add_card(s1, Inches(0.8), card_y, card_w, card_h, bg_hex="19414D", border_hex="265A68")

    tb_q = s1.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(10.9), Inches(1.4))
    tf_q = tb_q.text_frame
    tf_q.word_wrap = True
    p1 = tf_q.paragraphs[0]
    p1.text = "How can HSL city-bike operators anticipate where bikes deplete"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_PRIMARY_LIGHT

    p2 = tf_q.add_paragraph()
    p2.text = "and docks saturate across 457 stations in Helsinki and Espoo?"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_LIGHT_ACCENT
    p2.space_before = Pt(4)

    # 3 Focus Area Badges inside the card
    focus_y = Inches(3.7)
    focus_w = Inches(3.45)
    focus_h = Inches(1.5)
    focus_items = [
        ("Macro Seasonality", "14 operating months (2024–2025)\nUnimodal summer peak & shoulder contraction"),
        ("Commuter Tidal Swings", "+78% evening rush surge\nOpposing morning vs. evening tidal flows"),
        ("Operational Triage", "Identifying structural transit sinks\nSame-month baseline for fleet sizing")
    ]
    for idx, (f_title, f_sub) in enumerate(focus_items):
        fx = Inches(1.2 + idx * 3.75)
        add_card(s1, fx, focus_y, focus_w, focus_h, bg_hex="12313A", border_hex="265A68")
        tb = s1.shapes.add_textbox(fx + Inches(0.18), focus_y + Inches(0.15), focus_w - Inches(0.36), focus_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f_title
        p.font.name = FONT_HEADING
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = COLOR_LIGHT_ACCENT
        p_sub = tf.add_paragraph()
        p_sub.text = f_sub
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_LIGHT_MUTED
        p_sub.space_before = Pt(4)

    # Footer Metadata
    tb_foot = s1.shapes.add_textbox(Inches(0.8), Inches(6.05), Inches(10.5), Inches(0.55))
    tf_foot = tb_foot.text_frame
    tf_foot.word_wrap = True
    p_auth = tf_foot.paragraphs[0]
    p_auth.text = "Authors: Chenyu Wu  ·  Jizhou Wang  ·  Jussi Honkio"
    p_auth.font.name = FONT_BODY
    p_auth.font.size = Pt(13)
    p_auth.font.bold = True
    p_auth.font.color.rgb = COLOR_PRIMARY_LIGHT

    p_meta = tf_foot.add_paragraph()
    p_meta.text = "University of Helsinki · Introduction to Data Science · Canvas Mini-Project Spotlight Session"
    p_meta.font.name = FONT_BODY
    p_meta.font.size = Pt(10.5)
    p_meta.font.color.rgb = COLOR_LIGHT_MUTED
    p_meta.space_before = Pt(2)

    set_speaker_notes(s1, "0:00-0:20", "20 seconds",
                      "Good morning. City-bike operators in Helsinki face a daily rebalancing headache: docks run empty during morning commutes and overflow by evening. Across nearly five million cleaned trips in 2024 and 2025, our goal is helping HSL planners triage critical stations before service disruptions occur.")

    # =========================================================================
    # SLIDE 2: Station-Month Demand Heatmap (Light Theme)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_LIGHT_BG)
    add_slide_header(s2, 2, "Seasonal Concentration", "Summer Peaks at Nearly 500k Monthly Trips, Anchored by Major Rail Hubs",
                     "Station-Month Departures Across Two Full Seasons (April–October, 2024 & 2025)")

    # Core Visual: fig2_station_month_demand_heatmap.png
    fig2_path = os.path.join(fig_dir, "fig2_station_month_demand_heatmap.png")
    if os.path.exists(fig2_path):
        s2.shapes.add_picture(fig2_path, Inches(0.8), Inches(1.8), Inches(6.9), Inches(5.0))
    else:
        add_card(s2, Inches(0.8), Inches(1.8), Inches(6.9), Inches(5.0))

    # Right 2 Callouts
    r_left = Inches(7.95)
    r_width = Inches(4.58)

    # Callout 1
    add_card(s2, r_left, Inches(1.8), r_width, Inches(2.35), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb1 = s2.shapes.add_textbox(r_left + Inches(0.2), Inches(1.95), r_width - Inches(0.4), Inches(2.05))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Sharp Unimodal Summer Envelope"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL_ACCENT

    bullets1 = [
        ("Summer Peak: ", "Monthly demand peaks in July/August at ~450k–492k trips, then contracts sharply by over 50% in shoulder months (April: 162k–243k; October: 198k–207k)."),
        ("Regional Share: ", "Helsinki commands 88.8% of total ridership; Espoo accounts for 11.2% centered around metro stations and universities.")
    ]
    for b_title, b_txt in bullets1:
        p = tf1.add_paragraph()
        p.space_before = Pt(5)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    # Callout 2
    add_card(s2, r_left, Inches(4.35), r_width, Inches(2.45), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb2 = s2.shapes.add_textbox(r_left + Inches(0.2), Inches(4.5), r_width - Inches(0.4), Inches(2.15))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Transit Hub Sinks & Weather Context"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL_ACCENT

    bullets2 = [
        ("Transit Anchors: ", "Top stations (Pasila station, Central Railway, Kalasatama, Itämerentori) sustain over 5,000–9,000 monthly departures throughout summer."),
        ("Descriptive Weather: ", "Daily ridership correlates with mean temperature (r = +0.74) and rain (r = -0.25). Reflects seasonal daylight (19h June vs. 9h Oct) and holidays; strictly non-causal.")
    ]
    for b_title, b_txt in bullets2:
        p = tf2.add_paragraph()
        p.space_before = Pt(5)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    set_speaker_notes(s2, "0:20-0:55", "35 seconds",
                      "Looking at the thirty busiest stations across fourteen operating months, ridership follows a steep summer peak in July and August, contracting by more than half in shoulder months. Helsinki accounts for eighty-nine percent of volume, anchored by major rail hubs like Pasila and Central Railway Station. Daily trips correlate with warm summer days, but this reflects holiday schedules and long Nordic daylight rather than direct causation. This volume profile informs seasonal fleet sizing.")

    # =========================================================================
    # SLIDE 3: Commuter Peak Asymmetry & Tidal Reversals (Light Theme)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_LIGHT_BG)
    add_slide_header(s3, 3, "Intraday Commute Dynamics", "Weekday Evening Demand Surges +78%, Reversing Station Net Flows",
                     "Standardized Peak Windows (07:00–09:00 vs. 16:00–18:00) Reveal Polarized Commuter Swings")

    # Core Visual: fig6_morning_vs_evening_peak_station_comparison.png
    fig6_path = os.path.join(fig_dir, "fig6_morning_vs_evening_peak_station_comparison.png")
    if os.path.exists(fig6_path):
        s3.shapes.add_picture(fig6_path, Inches(0.8), Inches(1.8), Inches(7.4), Inches(5.0))
    else:
        add_card(s3, Inches(0.8), Inches(1.8), Inches(7.4), Inches(5.0))

    # Right 2 Callouts
    r_left3 = Inches(8.45)
    r_width3 = Inches(4.08)

    # Callout 1: Evening Rush Surge
    add_card(s3, r_left3, Inches(1.8), r_width3, Inches(2.35), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb3_1 = s3.shapes.add_textbox(r_left3 + Inches(0.2), Inches(1.95), r_width3 - Inches(0.4), Inches(2.05))
    tf3_1 = tb3_1.text_frame
    tf3_1.word_wrap = True
    p = tf3_1.paragraphs[0]
    p.text = "Evening Rush Surge (+78% to +96%)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL_ACCENT

    bullets3_1 = [
        ("Helsinki 2025: ", "Morning 1,208 trips/day → Evening 2,154 trips/day (+78.4% surge)."),
        ("Espoo 2025: ", "Morning 141 trips/day → Evening 276 trips/day (+95.9% surge)."),
        ("Behavioral Driver: ", "Morning trips are utilitarian work commutes. Evening trips blend homeward travel with retail, dining, and recreation under evening daylight.")
    ]
    for b_title, b_txt in bullets3_1:
        p = tf3_1.add_paragraph()
        p.space_before = Pt(4)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    # Callout 2: Tidal Reversals
    add_card(s3, r_left3, Inches(4.35), r_width3, Inches(2.45), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb3_2 = s3.shapes.add_textbox(r_left3 + Inches(0.2), Inches(4.5), r_width3 - Inches(0.4), Inches(2.15))
    tf3_2 = tb3_2.text_frame
    tf3_2.word_wrap = True
    p = tf3_2.paragraphs[0]
    p.text = "Diurnal Commuter Tidal Reversals"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL_ACCENT

    bullets3_2 = [
        ("Residential Feeders: ", "Sompasaari empties in the morning (-7,973 net flow) and fills up in the evening (+2,808 net flow)."),
        ("Workplace Centers: ", "Salmisaarenranta fills in the morning (+7,343 net flow) and empties in the evening (-5,244 net flow)."),
        ("Transit Interchanges: ", "Pasila rail station remains in deficit all day (-2.6k morning, -2.6k evening).")
    ]
    for b_title, b_txt in bullets3_2:
        p = tf3_2.add_paragraph()
        p.space_before = Pt(4)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    set_speaker_notes(s3, "0:55-1:30", "35 seconds",
                      "Intraday patterns show that weekday evening peaks generate seventy-eight to ninety-six percent more trips than morning peaks. Simultaneously, stations undergo sharp tidal reversals. Residential docks like Sompasaari experience severe morning deficits as commuters leave, but accumulate heavy surpluses by evening. Conversely, workplace centers like Salmisaarenranta fill up in the morning and empty out after work. Meanwhile, Pasila rail station operates in continuous deficit throughout the entire day. These commuter swings dictate where rebalancing vans should stage.")

    # =========================================================================
    # SLIDE 4: Spatial Rebalancing Imbalance Map (Light Theme)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_LIGHT_BG)
    add_slide_header(s4, 4, "Rebalancing Triage", "Directional Net Flow Pinpoints Systemic Rebalancing Bottlenecks",
                     "Cumulative Net Flow (Returns - Departures) Across 454 Coordinate Stations (2024–2025)")

    # Core Visual: fig3_station_net_flow_map.png
    fig3_path = os.path.join(fig_dir, "fig3_station_net_flow_map.png")
    if os.path.exists(fig3_path):
        s4.shapes.add_picture(fig3_path, Inches(0.8), Inches(1.8), Inches(6.9), Inches(5.0))
    else:
        add_card(s4, Inches(0.8), Inches(1.8), Inches(6.9), Inches(5.0))

    # Right 2 Callouts
    r_left4 = Inches(7.95)
    r_width4 = Inches(4.58)

    # Callout 1: Deficit Sinks
    add_card(s4, r_left4, Inches(1.8), r_width4, Inches(2.35), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb4_1 = s4.shapes.add_textbox(r_left4 + Inches(0.2), Inches(1.95), r_width4 - Inches(0.4), Inches(2.05))
    tf4_1 = tb4_1.text_frame
    tf4_1.word_wrap = True
    p = tf4_1.paragraphs[0]
    p.text = "Deficit Sinks (Red, Bike Depletion)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_CORAL_ACCENT

    bullets4_1 = [
        ("Pasila Rail Interchange: ", "Chronic primary sink with -11,014 net trips (capacity: 40); disembarking train commuters bike to offices."),
        ("Radial Arterials: ", "Mäkelänkatu (-5,275), Opastinsilta (-5,049), and Karhupuisto (-4,421) suffer rapid bicycle exhaustion."),
        ("Operational Implication: ", "Priority candidates for pre-staging bicycle supplies before morning rush.")
    ]
    for b_title, b_txt in bullets4_1:
        p = tf4_1.add_paragraph()
        p.space_before = Pt(4)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    # Callout 2: Surplus Sources
    add_card(s4, r_left4, Inches(4.35), r_width4, Inches(2.45), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb4_2 = s4.shapes.add_textbox(r_left4 + Inches(0.2), Inches(4.5), r_width4 - Inches(0.4), Inches(2.15))
    tf4_2 = tb4_2.text_frame
    tf4_2.word_wrap = True
    p = tf4_2.paragraphs[0]
    p.text = "Surplus Sources (Blue, Dock Congestion)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_BLUE_ACCENT

    bullets4_2 = [
        ("Destination Accumulators: ", "Waterfront and dining clusters: Unioninkatu (+3,474), Kanavaranta (+3,081), Kalasatama (+2,140)."),
        ("Dock Saturation Risk: ", "High risk of return blocking where riders cannot find open slots to terminate trips."),
        ("Triage Distinction: ", "Net flow measures passenger drift, NOT exact truck loads. Van dispatch requires live dock occupancy telemetry.")
    ]
    for b_title, b_txt in bullets4_2:
        p = tf4_2.add_paragraph()
        p.space_before = Pt(4)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    set_speaker_notes(s4, "1:30-2:05", "35 seconds",
                      "Mapping cumulative net flow across the network highlights structural rebalancing sinks in red and surplus sources in blue. Pasila railway station is the primary deficit bottleneck, accumulating an eleven-thousand trip deficit over two seasons. While this macro drift identifies priority candidates for rebalancing attention, it reflects passenger flow rather than exact physical bike inventory or rigid truck dispatch orders.")

    # =========================================================================
    # SLIDE 5: Predictive Benchmarks for Fleet Sizing (Light Theme)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_LIGHT_BG)
    add_slide_header(s5, 5, "Demand Forecasting", "Previous-Year Same-Month Baseline Minimizes Demand Forecast Error",
                     "2025 Out-of-Time Backtest (N=2,718 Matched Station-Months; Unit: Trips / Station-Month)")

    # Core Visual: fig7_forecast_evaluation_actual_vs_baseline_2025.png
    fig7_path = os.path.join(fig_dir, "fig7_forecast_evaluation_actual_vs_baseline_2025.png")
    if os.path.exists(fig7_path):
        s5.shapes.add_picture(fig7_path, Inches(0.8), Inches(1.8), Inches(7.4), Inches(5.0))
    else:
        add_card(s5, Inches(0.8), Inches(1.8), Inches(7.4), Inches(5.0))

    # Right 2 Callouts
    r_left5 = Inches(8.45)
    r_width5 = Inches(4.08)

    # Callout 1: Baseline Superiority
    add_card(s5, r_left5, Inches(1.8), r_width5, Inches(2.35), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb5_1 = s5.shapes.add_textbox(r_left5 + Inches(0.2), Inches(1.95), r_width5 - Inches(0.4), Inches(2.05))
    tf5_1 = tb5_1.text_frame
    tf5_1.word_wrap = True
    p = tf5_1.paragraphs[0]
    p.text = "Baseline Lowest Volume Error (17.6%)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL_ACCENT

    bullets5_1 = [
        ("Historical Baseline: ", "Same-month previous-year achieves 17.58% WAPE (MAE: 141.9 trips/month)."),
        ("Absorbs Nordic Shifts: ", "Naturally aligns with solar daylight and academic calendars without transitional lag delay, beating Decision Trees (24.7%) and Ridge (28.0%)."),
        ("Macro Sizing Role: ", "Highly effective for seasonal fleet sizing and monthly station quotas.")
    ]
    for b_title, b_txt in bullets5_1:
        p = tf5_1.add_paragraph()
        p.space_before = Pt(4)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    # Callout 2: Complementary Utility
    add_card(s5, r_left5, Inches(4.35), r_width5, Inches(2.45), bg_hex="FFFFFF", border_hex="DCE6E8")
    tb5_2 = s5.shapes.add_textbox(r_left5 + Inches(0.2), Inches(4.5), r_width5 - Inches(0.4), Inches(2.15))
    tf5_2 = tb5_2.text_frame
    tf5_2.word_wrap = True
    p = tf5_2.paragraphs[0]
    p.text = "Complementary Tools & Methodological Unit"
    p.font.name = FONT_HEADING
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEAL_ACCENT

    bullets5_2 = [
        ("Ridge for Deficit Ranks: ", "Ridge regression captures 65%–80% of Top-20 deficit stations in May–August (Spearman ρ = 0.76)."),
        ("Metric Definition: ", "MAE is measured in completed trips/month, NOT physical bicycle stock."),
        ("Preliminary Benchmark: ", "Evaluated on a single 2025 backtest season; serves as an empirical reference, not definitive proof.")
    ]
    for b_title, b_txt in bullets5_2:
        p = tf5_2.add_paragraph()
        p.space_before = Pt(4)
        r = p.add_run()
        r.text = "• " + b_title
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_PRIMARY_DARK
        r2 = p.add_run()
        r2.text = b_txt
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = COLOR_MUTED_SLATE

    set_speaker_notes(s5, "2:05-2:35", "30 seconds",
                      "When forecasting 2025 monthly demand, using the previous year's same month achieved the lowest volume error at 17.6% WAPE. The baseline naturally absorbs Nordic seasonal shifts without transitional delay. Meanwhile, Ridge regression helps screen high-deficit stations. This single-season test provides an empirical benchmark for fleet sizing, measured in monthly trip events, not missing bicycles.")

    # =========================================================================
    # SLIDE 6: Operational Recommendations & Guardrails (Light Theme)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_LIGHT_BG)
    add_slide_header(s6, 6, "Operational Conclusions", "Actionable Guidelines & Methodological Guardrails for Operators",
                     "Empirical Recommendations for Seasonal Fleet Sizing, Triage & Future Telemetry")

    # Top: 3 Operator Action Cards
    act_w = Inches(3.75)
    act_h = Inches(3.0)
    act_y = Inches(1.8)
    actions = [
        ("1. Seasonal Fleet Sizing", COLOR_TEAL_ACCENT,
         "Historical Baseline for Procurement",
         "Use the previous-year same-month baseline (17.6% WAPE) to establish macro seasonal bike fleet contracts and monthly depot allocations. It naturally captures northern climate shifts without lag error."),
        ("2. Rebalancing Route Triage", COLOR_CORAL_ACCENT,
         "Pre-Stage Prior to 16:00 Rush",
         "Target chronic transit sinks (Pasila rail hub, -11k net flow). Explore pre-staging bicycle redistribution prior to the afternoon peak (e.g. before 15:30) to absorb the +78% evening surge."),
        ("3. Connect Live Telemetry", COLOR_BLUE_ACCENT,
         "Integrate Real-Time Dock Sensors",
         "Pair monthly triage screening with real-time 15-minute dock occupancy feeds before issuing physical van dispatch orders. Net flow reflects macro passenger drift, not live dock fullness.")
    ]
    for idx, (a_title, a_color, a_sub, a_desc) in enumerate(actions):
        ax = Inches(0.8 + idx * 4.0)
        add_card(s6, ax, act_y, act_w, act_h, bg_hex="FFFFFF", border_hex="DCE6E8")
        tb = s6.shapes.add_textbox(ax + Inches(0.2), act_y + Inches(0.18), act_w - Inches(0.4), act_h - Inches(0.36))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = a_title
        p.font.name = FONT_HEADING
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = a_color

        p_sub = tf.add_paragraph()
        p_sub.text = a_sub
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(11)
        p_sub.font.bold = True
        p_sub.font.color.rgb = COLOR_PRIMARY_DARK
        p_sub.space_before = Pt(4)

        p_desc = tf.add_paragraph()
        p_desc.text = a_desc
        p_desc.font.name = FONT_BODY
        p_desc.font.size = Pt(10)
        p_desc.font.color.rgb = COLOR_MUTED_SLATE
        p_desc.space_before = Pt(6)

    # Bottom Full-Width Guardrail Card
    bot_y = Inches(5.0)
    bot_w = Inches(11.73)
    bot_h = Inches(1.75)
    add_card(s6, Inches(0.8), bot_y, bot_w, bot_h, bg_hex="12313A", border_hex="12313A")

    tb_g = s6.shapes.add_textbox(Inches(1.05), bot_y + Inches(0.12), bot_w - Inches(0.5), bot_h - Inches(0.24))
    tf_g = tb_g.text_frame
    tf_g.word_wrap = True

    p = tf_g.paragraphs[0]
    p.text = "Essential Methodological Boundaries (What the Data Does and Does Not Show):"
    p.font.name = FONT_HEADING
    p.font.size = Pt(12.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_LIGHT_ACCENT

    guards = [
        "• Weather = Retrospective FMI observations, strictly excluded from 2025 predictions; correlations reflect seasonal co-movement, not direct causality.",
        "• MAE Unit = Trips per station-month, not missing bicycles. Bicycles circulate across multiple trips throughout each day.",
        "• Net Flow ≠ Van Dispatch Workloads. Reflects 30-day directional passenger drift; diurnal reversals partially offset daytime flows.",
        "• Single Test Cycle = 2025 represents an exploratory out-of-time benchmark; no claims of statistical significance or long-term superiority."
    ]
    for g_text in guards:
        p = tf_g.add_paragraph()
        p.text = g_text
        p.font.name = FONT_BODY
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_PRIMARY_LIGHT
        p.space_before = Pt(2)

    set_speaker_notes(s6, "2:35-3:00", "25 seconds",
                      "To conclude, operators should use the historical baseline for seasonal fleet sizing and net-flow rankings to prioritize rebalancing routes, such as pre-staging before the 16:00 evening surge. Connecting real-time dock telemetry is the essential next step before dispatching redistribution vans. Thank you, and we welcome your questions.")

    prs.save(out_pptx_path)
    print(f"Successfully generated Spotlight presentation: {out_pptx_path}")
    print(f"Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_file = os.path.join(project_dir, "HSL_Bike_Heatmap_Presentation.pptx")
    out_file = os.path.join(project_dir, "HSL_Bike_Heatmap_Presentation_Spotlight.pptx")
    build_spotlight_presentation(base_file, out_file)
