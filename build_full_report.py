"""
Complete generator for the professionally updated project report in DOCX format:
C:\\Users\\Lenovo\\Desktop\\Smart_Goggle_AIML_Updated_Report.docx
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def generate_report():
    doc = docx.Document()

    # 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Base styling
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11.5)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    def set_cell_shading(cell, color_hex):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for margin, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
            node = OxmlElement(margin)
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    def format_table(table, col_widths, headers, data, header_bg='1F4E79'):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        # Header Row
        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = header_text
            set_cell_shading(hdr_cells[i], header_bg)
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=130, right=130)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
            p.runs[0].font.size = Pt(10)

        # Data Rows
        for r_idx, row_data in enumerate(data):
            row_cells = table.add_row().cells
            bg_color = 'F2F4F7' if r_idx % 2 == 1 else 'FFFFFF'
            for c_idx, cell_value in enumerate(row_data):
                row_cells[c_idx].text = str(cell_value)
                set_cell_shading(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=70, bottom=70, left=110, right=110)
                p = row_cells[c_idx].paragraphs[0]
                p.runs[0].font.size = Pt(9.5)
                if c_idx == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = width

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(31, 78, 121)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(46, 117, 182)
        return p

    def add_heading_3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11.5)
        r.font.bold = True
        return p

    def add_body(text, space_after=4):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(space_after)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11.5)
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(4)
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Times New Roman'
        r_b.font.size = Pt(11.5)
        r_b.font.bold = True
        r_t = p.add_run(text)
        r_t.font.name = 'Times New Roman'
        r_t.font.size = Pt(11.5)
        return p

    def add_figure(img_path, caption_text, width=Inches(5.8)):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(4)
            r = p_img.add_run()
            r.add_picture(img_path, width=width)
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(10)
        r_cap = p_cap.add_run(caption_text)
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10)
        r_cap.font.italic = True
        r_cap.font.bold = True

    def add_table_caption(caption_text):
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_cap.paragraph_format.space_before = Pt(10)
        p_cap.paragraph_format.space_after = Pt(4)
        r_cap = p_cap.add_run(caption_text)
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10)
        r_cap.font.bold = True

    def add_equation(eq_text, eq_number_str):
        table = doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        row = table.rows[0]
        row.cells[0].width = Inches(5.7)
        row.cells[1].width = Inches(0.8)
        
        p_eq = row.cells[0].paragraphs[0]
        p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_eq = p_eq.add_run(eq_text)
        r_eq.font.name = 'Cambria Math'
        r_eq.font.size = Pt(11)
        r_eq.font.italic = True
        
        p_num = row.cells[1].paragraphs[0]
        p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_num = p_num.add_run(eq_number_str)
        r_num.font.name = 'Times New Roman'
        r_num.font.size = Pt(11)
        r_num.font.bold = True

    img_dir = r'C:\Users\Lenovo\Desktop\aiml_project_googke\report_extracted_images'

    # =========================================================================
    # 1. TITLE PAGE
    # =========================================================================
    logo_path = os.path.join(img_dir, 'img_10.jpg')
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_after = Pt(8)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.8))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Pimpri Chinchwad Education Trust's\n")
    r.font.size = Pt(13)
    r.font.bold = True
    r = p.add_run("Pimpri Chinchwad College of Engineering\n")
    r.font.size = Pt(16)
    r.font.bold = True
    r = p.add_run("Sector No. 26, Pradhikaran, Nigdi, Pune – 411044\n")
    r.font.size = Pt(11)
    r = p.add_run("An Autonomous Institute Approved by AICTE and Affiliated to SPPU, Pune\n\n")
    r.font.size = Pt(10.5)
    r.font.italic = True
    r = p.add_run("Department of Information Technology\n\n")
    r.font.size = Pt(14)
    r.font.bold = True

    r = p.add_run("Artificial Intelligence and Machine Learning Mini Project Report\n")
    r.font.size = Pt(13)
    r.font.bold = True
    r = p.add_run("of\nT. Y. B. Tech\n")
    r.font.size = Pt(12)
    r = p.add_run("Academic Year: 2026-27 | Semester - I\n\n")
    r.font.size = Pt(12)

    r = p.add_run("Smart Goggle: AI-Based Personalized Health and Environment Monitoring System\n\n")
    r.font.size = Pt(17)
    r.font.bold = True
    r.font.color.rgb = RGBColor(31, 78, 121)

    r = p.add_run("Submitted By:\n")
    r.font.size = Pt(12)
    r.font.bold = True

    t_auth = doc.add_table(rows=1, cols=2)
    format_table(
        t_auth,
        [Inches(2.5), Inches(3.5)],
        ["PRN No.", "Name of the Student"],
        [
            ["124B1F106", "Sanket Yamgar"],
            ["124B1F107", "Omkar Palve"],
            ["124B1F109", "Mayank Pawar"]
        ]
    )

    doc.add_page_break()

    # =========================================================================
    # 2. CERTIFICATE
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(28)
    p.paragraph_format.space_after = Pt(24)
    r = p.add_run("CERTIFICATE\n")
    r.font.size = Pt(16)
    r.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.4
    p.add_run(
        "This is to certify that the mini-project report entitled "
        "\"Smart Goggle: AI-Based Personalized Health and Environment Monitoring System\" "
        "has been successfully completed by Sanket Yamgar (PRN: 124B1F106), "
        "Omkar Palve (PRN: 124B1F107), and Mayank Pawar (PRN: 124B1F109) in partial fulfillment of the requirements "
        "for the degree of Third Year of Bachelor of Technology (T.Y. B.Tech) in Information Technology "
        "under the course Artificial Intelligence and Machine Learning Laboratory at Pimpri Chinchwad College of "
        "Engineering, Nigdi, Pune, affiliated to Savitribai Phule Pune University (SPPU), during the academic year 2026-27 (Semester-I).\n\n"
        "This work is an authentic record of the work carried out under our supervision and complies with all academic "
        "and ethical guidelines stipulated by the Department."
    )

    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_before = Pt(64)
    p_sig.paragraph_format.space_after = Pt(12)
    sig_table = doc.add_table(rows=2, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in sig_table.rows:
        r.cells[0].width = Inches(3.2)
        r.cells[1].width = Inches(3.2)
    sig_table.rows[0].cells[0].text = "______________________________\nInternal Project Guide\nDepartment of Information Technology\nPCCOE, Pune"
    sig_table.rows[0].cells[1].text = "______________________________\nHead of Department\nDepartment of Information Technology\nPCCOE, Pune"
    sig_table.rows[1].cells[0].text = "\nDate: ________________________"
    sig_table.rows[1].cells[1].text = "\nPlace: Nigdi, Pune"

    doc.add_page_break()

    # =========================================================================
    # 3. ABSTRACT (Proper Academic Format + Keywords)
    # =========================================================================
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Smart Goggle: AI-Based Personalized Health and Environment Monitoring System\n")
    r.font.size = Pt(15)
    r.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(12)
    r = p.add_run("ABSTRACT\n")
    r.font.size = Pt(13)
    r.font.bold = True

    add_body(
        "Urban populations are routinely exposed to hazardous atmospheric air pollution without real-time, localized awareness of ambient pollutant concentrations. "
        "Simultaneously, individual physiological responses—including cardiovascular fluctuations, autonomic stress elevations, and peripheral thermal variations—routinely go undetected. "
        "Commercial technologies fragment these complementary signals, treating personal fitness trackers and environmental air-quality indices as disconnected silos. "
        "To bridge this gap, this project develops Smart Goggle: an end-to-end wearable Internet of Things (IoT) prototype that couples continuous physiological biosensing "
        "with geolocation-aware atmospheric air-quality intelligence, dual-stream machine learning classification, and Explainable Artificial Intelligence (XAI)."
    )
    add_body(
        "The system incorporates an ESP32 microcontroller integrated with an optical photoplethysmogram sensor (MAX30102) and an infrared non-contact thermopile (MLX90614) "
        "communicating over an optimized 100 kHz I2C bus. Firmware pulse-processing implements a moving DC baseline and a relative-interval buffer to reject optical motion artifacts, "
        "streaming standardized JSON packets over Bluetooth Low Energy (BLE) GATT notifications to a cross-platform Flutter mobile application. "
        "The mobile device resolves hardware GPS coordinates and queries the Open-Meteo Air Quality API for six criteria pollutants (PM2.5, PM10, NO2, CO, SO2, O3), "
        "forwarding synchronized payloads to a FastAPI cloud backend for asynchronous inference."
    )
    add_body(
        "For environmental classification, five candidate machine-learning and deep-learning architectures—Random Forest, XGBoost, Extra Trees, CatBoost, and TabNet—were "
        "benchmarked on a leak-free 70/15/15 stratified partition of 24,850 Indian Central Pollution Control Board (CPCB) records. "
        "Random Forest established the highest overall test accuracy (80.26%) and weighted F1-score (80.03%), closely tracked by XGBoost (79.96%) and Extra Trees (79.61%), "
        "with Extra Trees achieving the highest macro-averaged F1-score (78.31%) due to superior recall on severe and clean atmospheric extremes. "
        "TabNet attained 76.39% accuracy, illustrating that tree-based orthogonal splits outperform tabular neural attention on axis-aligned environmental breakpoints. "
        "Concurrently, physiological stress classification evaluated under strict subject-wise GroupSplit across 35 unseen human participants achieved 48.69% accuracy, "
        "characterizing real-world cross-subject autonomic variability. Local predictions are rendered transparent via shap.TreeExplainer directional attributions, "
        "and synthesized into an operational 0–100 composite risk score. Smart Goggle provides an explainable, non-diagnostic prototype for personalized environmental health awareness."
    )

    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(8)
    r_kwh = p_kw.add_run("Keywords: ")
    r_kwh.font.bold = True
    p_kw.add_run("Wearable Computing, Ambient Air Quality Index (AQI), Physiological Stress Monitoring, Machine Learning, Explainable AI (XAI), SHAP, Internet of Things (IoT), Mobile Health.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    add_heading_1("1. Introduction")
    
    add_heading_2("1.1 Background")
    add_body(
        "Ambient air pollution represents a critical public health hazard across urban regions, particularly in rapidly industrializing metropolitan areas of India. "
        "Fine particulate matter (PM2.5 and PM10), nitrogen dioxide (NO2), tropospheric ozone (O3), carbon monoxide (CO), and sulfur dioxide (SO2) are clinically "
        "linked to acute respiratory irritation, pulmonary inflammation, and aggravated cardiovascular distress. "
        "Despite severe exposure risks, the vast majority of citizens rely exclusively on regional government monitoring stations that publish city-wide 24-hour averages. "
        "These coarse readings fail to capture hyper-local spatial variations caused by vehicular corridors, industrial emissions, and micro-climates."
    )
    add_body(
        "Simultaneously, the human autonomic nervous system responds dynamically to physical exertion, psychological stress, and environmental thermal stressors through "
        "fluctuations in instantaneous heart rate, heart rate variability (HRV), and peripheral skin temperature. "
        "While low-cost wearable sensors enable non-invasive acquisition of physiological vitals, existing consumer devices maintain total isolation between ambient environmental data "
        "and biological strain. Smart Goggle addresses this disconnect by developing an integrated, edge-to-cloud wearable monitoring platform that bridges physiological vital tracking, "
        "geolocated air pollution ingestion, machine-learning classification, and explainable risk synthesis."
    )

    add_heading_2("1.2 Problem Definition")
    add_body(
        "Environmental monitoring and biometric vital tracking are conventionally partitioned into disparate consumer domains. "
        "A user observing an elevated heart rate cannot readily determine whether the cardiovascular reaction is induced by ambient thermal stress, acute air pollution exposure, "
        "psychological workload, or natural physical exertion. The core problem addressed in this project is: "
        "To construct an end-to-end, low-cost prototype system that captures heart rate and peripheral temperature from a wearable smart goggle band, "
        "dynamically determines localized air pollution via mobile GPS, classifies environmental and physiological stress tiers using machine learning, "
        "renders predictions interpretable through local feature attributions, and provides a synthesized, unified health-risk indicator."
    )

    add_heading_2("1.3 Objectives")
    add_bullet("1. Wearable Edge Acquisition: ", "Design and fabricate an ESP32-based wearable module that captures optical pulse and infrared contactless temperature, executing real-time digital filtering and streaming telemetry via Bluetooth Low Energy (BLE).")
    add_bullet("2. Environmental Classification Pipeline: ", "Train and benchmark multi-class machine-learning models to predict Indian National AQI categories strictly using live-available criteria pollutants (PM2.5, PM10, NO2, CO, SO2, O3).")
    add_bullet("3. Subject-Independent Stress Classification: ", "Train a physiological stress classifier evaluated under a strict subject-wise grouped split across independent human participants to prevent over-optimistic biometric memorization.")
    add_bullet("4. Model Architecture Benchmarking: ", "Perform a comprehensive comparative evaluation across five distinct model families—Random Forest, XGBoost, Extra Trees, CatBoost, and TabNet—under a standardized 70/15/15 stratified protocol.")
    add_bullet("5. Explainable AI (XAI) Integration: ", "Incorporate TreeSHAP to generate real-time directional feature attributions for every prediction, demystifying the black-box classification behavior.")
    add_bullet("6. Multi-Source Risk Synthesis: ", "Implement a rule-based synthesis engine combining environmental hazard levels, autonomic stress states, and hardware safety flags into an operational 0–100 composite risk index.")
    add_bullet("7. Mobile Dashboard Visualization: ", "Develop a cross-platform Flutter application providing real-time vital monitoring, environmental alerts, interactive SHAP waterfalls, and integration debug telemetry.")

    add_heading_2("1.4 Scope and Limitations")
    add_body(
        "The Smart Goggle system is engineered strictly as an educational and research prototype for personal health awareness and environmental risk indication. "
        "It does not constitute a certified medical diagnostic device, does not diagnose chronic disease, and does not provide clinical therapeutic recommendations. "
        "The firmware deliberately omits blood oxygen saturation (SpO2) computation because the MAX30102 sensor lacks empirical multi-wavelength calibration on this custom board; "
        "consequently, SpO2 is transparently reported as unavailable (null/N/A). "
        "All physiological and air-quality models are trained on established public benchmarks and evaluated on held-out empirical partitions."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 2: LITERATURE SURVEY (Point format - No Table!)
    # =========================================================================
    add_heading_1("2. Literature Survey")
    add_body(
        "To establish a rigorous theoretical and empirical foundation for the Smart Goggle architecture, an extensive literature survey was conducted. "
        "The survey encompasses four critical research areas: wearable physiological stress benchmarks, tabular machine-learning algorithms, "
        "Explainable Artificial Intelligence (XAI) frameworks, and ambient air quality indexing standards. "
        "The key contributions, methodologies, and limitations of existing literature are summarized in the following structured points:"
    )

    add_heading_2("2.1 Wearable Physiological Sensing and Stress Detection")
    add_bullet(
        "Schmidt et al. (2018) [1] — WESAD Multi-Modal Dataset: ",
        "Introduced the Wearable Stress and Affect Detection (WESAD) dataset, comprising chest (RespiBAN) and wrist (Empatica E4) physiological recordings from 15 subjects under laboratory-induced baseline, stress (Trier Social Stress Test), and amusement conditions. "
        "The study demonstrated that photoplethysmogram (PPG), galvanic skin response (GSR), and skin temperature can distinguish stress states. "
        "Limitation: Data was captured using clinical-grade, high-cost sensors in tightly controlled laboratory environments, creating an acoustic and physiological gap when transferring models to low-cost consumer sensors."
    )
    add_bullet(
        "Koldijk et al. (2014) [2] — SWELL Knowledge Work Dataset: ",
        "Constructed the SWELL-KW multimodal dataset investigating stress under realistic office work environments (neutral tasks, email interruptions, and strict time pressure) across 25 knowledge workers. "
        "The authors proved that heart-rate variability (HRV) metrics and body temperature capture non-laboratory, everyday cognitive workload. "
        "Limitation: Experimental protocols differed substantially from WESAD, requiring label harmonization and sensor modality alignment for cross-dataset modeling."
    )
    add_bullet(
        "Can et al. (2020) [3] — Real-Life Stress Detection with Wearables: ",
        "Evaluated wearable stress recognition under natural everyday settings using heart rate and electrodermal activity. "
        "Crucially, the authors demonstrated that while subject-dependent classification yields accuracies exceeding 80%, subject-independent (leave-one-subject-out) classification drops to between 45% and 55% due to profound baseline physiological variance across individuals. "
        "Relevance: Confirms that our physiological stress model's 48.69% cross-subject accuracy represents a realistic, non-leaked benchmark."
    )
    add_bullet(
        "Böttcher et al. (2022) [4] — Generalization Challenges in Wearable Biosignals: ",
        "Benchmarked cross-subject transferability across multiple physiological datasets, highlighting that models trained without per-user baseline normalization suffer severe performance degradation when deployed on unseen users."
    )

    add_heading_2("2.2 Machine Learning Architectures for Tabular and Environmental Data")
    add_bullet(
        "Breiman (2001) [5] — Random Forest Classification: ",
        "Proposed Random Forests, constructing an ensemble of decorrelated decision trees grown on bootstrap data subsets with randomized feature candidate splits. "
        "Random Forest demonstrates extraordinary resilience against sensor noise, monotonic scaling invariance, and low hyperparameter sensitivity, serving as the primary production baseline in our pipelines."
    )
    add_bullet(
        "Chen and Guestrin (2016) [6] — XGBoost Gradient Boosting System: ",
        "Developed XGBoost, an optimized end-to-end tree boosting framework incorporating second-order Taylor expansion loss approximations, column subsampling, and explicit L1/L2 leaf weight regularization. "
        "XGBoost provides a high-efficiency baseline for structured tabular classification."
    )
    add_bullet(
        "Geurts et al. (2006) [7] — Extremely Randomized Trees (Extra Trees): ",
        "Introduced Extra Trees, which draws split thresholds purely at random from feature empirical ranges rather than identifying optimal mathematical cut-points. "
        "By trading structural bias for variance reduction, Extra Trees regularizes against extreme particulate outliers."
    )
    add_bullet(
        "Prokhorenkova et al. (2018) [8] — CatBoost Gradient Boosting: ",
        "Introduced CatBoost, implementing oblivious (symmetric) decision trees and ordered boosting to combat target leakage and prediction shift. "
        "Oblivious trees execute as binary table lookups, yielding microsecond inference speeds suitable for low-latency IoT pipelines."
    )
    add_bullet(
        "Arik and Pfister (2021) [9] — TabNet Neural Architecture: ",
        "Developed TabNet, a deep learning architecture for tabular data utilizing sequential decision steps with sparsemax attention masks to select salient features dynamically. "
        "TabNet offers end-to-end gradient learning and built-in interpretability but typically requires massive datasets to rival decision trees."
    )
    add_bullet(
        "Akiba et al. (2019) [10] — Optuna Hyperparameter Optimization: ",
        "Formulated Optuna, an asynchronous Tree-structured Parzen Estimator (TPE) Bayesian hyperparameter search framework used in this project to tune tree depths, learning rates, and regularization penalties on validation data."
    )

    add_heading_2("2.3 Explainable Artificial Intelligence (XAI) in Health Monitoring")
    add_bullet(
        "Lundberg and Lee (2017) [11] — Unified SHAP Framework: ",
        "Formulated SHAP (SHapley Additive exPlanations), unifying cooperative game-theoretic Shapley values with local additive explanation models to assign additive feature attribution values satisfying local accuracy, missingness, and consistency."
    )
    add_bullet(
        "Lundberg et al. (2020) [12] — Exact TreeSHAP for Tree Ensembles: ",
        "Developed TreeSHAP, an exact algorithm reducing the computational complexity of computing Shapley values for tree ensembles from exponential time O(2^d) to polynomial time O(TLD^2), making real-time local model explanations computationally feasible for live edge-cloud requests."
    )

    add_heading_2("2.4 Air Quality Standards and Environmental Health")
    add_bullet(
        "Central Pollution Control Board (CPCB, 2014) [13] — National Air Quality Index: ",
        "Defined India's official National AQI framework, establishing non-linear sub-index piecewise breakpoint equations across six criteria pollutants (PM2.5, PM10, NO2, CO, SO2, O3) and categorizing ambient air into six qualitative tiers."
    )
    add_bullet(
        "World Health Organization (WHO, 2021) [14] — Global Air Quality Guidelines: ",
        "Updated global health benchmarks for ambient particulate exposure, demonstrating that short-term PM2.5 spikes provoke immediate autonomic nervous system stress and systemic inflammatory cascades."
    )

    add_heading_2("2.5 Research Gap and Identified Problem Statement")
    add_body(
        "A comprehensive review of existing literature reveals a conspicuous structural gap: physiological wearable stress monitoring and ambient air pollution intelligence "
        "exist as completely separate academic and industrial fields. Wearable research (WESAD, SWELL) focuses exclusively on biometric laboratory tasks without ambient environmental context, "
        "while environmental monitoring systems record regional air pollution without tracking individual biological responses. "
        "Furthermore, student IoT systems frequently fabricate uncalibrated vital parameters (such as synthetic SpO2 values) and treat machine learning models as unexplainable black boxes. "
        "The Smart Goggle project bridges this gap by delivering a fully integrated, transparent system that: "
        "(1) correlates synchronized physiological vitals and geolocated environmental pollutants, "
        "(2) executes fair 5-model benchmarking on leak-free partitions, "
        "(3) provides real-time TreeSHAP local explanations for every inference, and "
        "(4) reports honest hardware limitations without fabricating clinical diagnostic claims."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 3: DATASETS USED
    # =========================================================================
    add_heading_1("3. Datasets Used")

    add_heading_2("3.1 Air Quality Data (Pipeline A)")
    add_body(
        "The environmental classification pipeline was trained on the official Indian National Air Quality dataset (city_day.csv), "
        "compiled from ground-based Continuous Ambient Air Quality Monitoring Stations (CAAQMS) operated by the Central Pollution Control Board (CPCB). "
        "The raw dataset comprises daily observations across major industrial and metropolitan Indian cities. "
        "Rows missing the ground-truth target label (AQI_Bucket) were removed, yielding exactly 24,850 clean, usable observational records."
    )
    add_body(
        "To ensure complete architectural compatibility with live inference, the feature space was strictly restricted to the six criteria pollutants provided by the Open-Meteo Air Quality API: "
        "fine particulate matter (PM2.5), coarse particulate matter (PM10), nitrogen dioxide (NO2), carbon monoxide (CO), sulfur dioxide (SO2), and surface ozone (O3). "
        "Secondary chemical species (e.g., Benzene, Toluene, Xylene) present in historical archives were discarded because they cannot be acquired at runtime. "
        "Crucially, the numerical AQI index column was strictly dropped prior to feature extraction; retaining numeric AQI would introduce fatal target leakage, "
        "enabling trivial mathematical lookup rather than authentic pollutant classification. "
        "Missing numerical features were imputed using the median computed strictly on the training partition (SimpleImputer(strategy='median')) to prevent distribution leakage."
    )

    add_heading_2("3.2 Physiological Data (Pipeline B)")
    add_body(
        "The physiological stress classification model utilizes a harmonized wearable biosignal benchmark synthesized from the open-source WESAD [1] and SWELL-KW [2] datasets. "
        "While WESAD includes 15 lab-stress subjects and SWELL includes 25 office-work subjects, 5 SWELL participants were excluded due to corrupted skin temperature channels "
        "and photoplethysmogram sensor dropouts, resulting in a robust, multi-subject cohort of exactly 35 independent human participants (15 WESAD + 20 SWELL)."
    )
    add_body(
        "Continuous heart-rate (BPM) and peripheral temperature streams were processed into sliding temporal windows of 30 seconds with 50% overlap. "
        "From each window, ten summary statistical features were extracted: mean heart rate (hr_mean), heart rate standard deviation (hr_std, serving as a time-domain HRV proxy), "
        "minimum heart rate (hr_min), maximum heart rate (hr_max), heart rate dynamic range (hr_range), median heart rate (hr_median), mean temperature (temp_mean), "
        "temperature standard deviation (temp_std), minimum temperature (temp_min), and maximum temperature (temp_max). "
        "Experimental conditions were mapped to a 3-tier ordinal stress state: Low (baseline/resting), Medium (time pressure/cognitive load), and High (acute stress/social stressor), "
        "as illustrated in Figure 1."
    )

    fig1_path = os.path.join(img_dir, 'img_5.png')
    add_figure(fig1_path, "Figure 1: Mapping of Wearable Biosignal Study Conditions to 3-Tier Stress Labels and Sliding-Window Statistical Features.")

    add_heading_2("3.3 Live Environmental Data")
    add_body(
        "At runtime, localized ambient air pollution is dynamically ingested via the Open-Meteo Air Quality REST API. "
        "The mobile application queries the smartphone's hardware GNSS receiver to resolve precise latitude and longitude coordinates. "
        "The FastAPI backend transmits these coordinates to the Open-Meteo service, receiving modeled hourly surface concentrations for PM2.5, PM10, NO2, CO, SO2, and O3. "
        "Units are normalized to match the CPCB training feature space before passing into the model pipeline."
    )

    add_heading_2("3.4 Dataset Summary")
    add_table_caption("Table 1: Summary of Environmental (AQI) and Physiological (Stress) Benchmark Datasets.")
    t_ds = doc.add_table(rows=1, cols=3)
    format_table(
        t_ds,
        [Inches(2.0), Inches(2.3), Inches(2.3)],
        ["Parameter", "Pipeline A (AQI Classification)", "Pipeline B (Stress Detection)"],
        [
            ["Data Source", "CPCB city_day.csv (Indian Stations)", "WESAD & SWELL-KW Harmonized Benchmark"],
            ["Total Sample Size", "24,850 usable records", "Sliding windows from 35 subjects"],
            ["Input Feature Space", "6 criteria pollutants (PM2.5, PM10, NO2, CO, SO2, O3)", "10 statistical window aggregates (HR & Temp)"],
            ["Target Variable", "6 AQI Buckets (Good to Severe)", "3 Stress Tiers (Low, Medium, High)"],
            ["Partitioning Scheme", "70/15/15 Stratified: 17,395 Train, 3,727 Val, 3,728 Test", "Subject-Wise GroupSplit across 35 independent subjects"],
            ["Leakage Safeguard", "Numeric AQI dropped; median imputer fitted on Train only", "Subject-wise separation; no shared participants"]
        ]
    )

    add_body(
        "In the held-out test partition (N = 3,728), the AQI classes exhibit pronounced natural class imbalance: "
        "Moderate: 1,325 samples (35.54%), Satisfactory: 1,234 samples (33.10%), Poor: 417 samples (11.19%), "
        "Very Poor: 350 samples (9.39%), Good: 201 samples (5.39%), and Severe: 201 samples (5.39%). "
        "This structural skew necessitates both balanced loss weighting during training and macro-averaged F1 evaluation."
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 4: SYSTEM DESIGN AND HARDWARE
    # =========================================================================
    add_heading_1("4. System Design and Hardware")

    add_heading_2("4.1 Overall Architecture")
    add_body(
        "The Smart Goggle architecture operates as a three-tier cyber-physical edge-cloud pipeline comprising: "
        "(1) the wearable hardware sensing tier, (2) the mobile edge aggregation tier, and (3) the cloud analytics and inference tier. "
        "The end-to-end system flow is illustrated in Figure 2."
    )

    fig2_path = os.path.join(img_dir, 'img_2.png')
    add_figure(fig2_path, "Figure 2: End-to-End System Architecture of Smart Goggle (Hardware Layer, BLE GATT, Flutter Mobile App, FastAPI Backend, and Output Synthesis).")

    add_heading_2("4.2 Hardware Components")
    add_table_caption("Table 2: Hardware Specifications and Sensor Pinout Configuration.")
    t_hw = doc.add_table(rows=1, cols=4)
    format_table(
        t_hw,
        [Inches(1.8), Inches(1.8), Inches(1.5), Inches(1.5)],
        ["Component", "Model / Spec", "Operating Role", "Hardware Interface"],
        [
            ["Microcontroller", "ESP32 WROOM-32 (Dual-core 240 MHz)", "I2C Master, Pulse Filtering, BLE Server", "Internal / 3.3V Logic"],
            ["Optical Biosensor", "Maxim Integrated MAX30102", "Photoplethysmogram (PPG) Pulse Sensing", "I2C (SDA: GPIO 21, SCL: GPIO 22)"],
            ["Thermal Sensor", "Melexis MLX90614 (GY-906 3.3V)", "Non-contact Infrared Skin Temperature", "Same I2C Bus (Address: 0x5A)"],
            ["Power Subsystem", "3.7V 500mAh LiPo + AMS1117 3.3V", "Regulated Power Supply with Decoupling", "Power Rail"]
        ]
    )

    add_body(
        "The MAX30102 sensor is configured with 4-sample averaging, dual Red + Infrared LED active mode, 100 Hz ADC sample rate, "
        "and a 411 µs pulse width. Both biosensors share the primary I2C bus on pins 21 (SDA) and 22 (SCL)."
    )

    add_heading_2("4.3 Firmware Implementation and Signal Processing")
    add_body(
        "The firmware is developed in C++ using the Arduino ESP32 core, executing sensor acquisition, digital filtering, and BLE transmission. "
        "A critical hardware engineering challenge involved I2C bus clock synchronization: initial experiments at 400 kHz caused severe NACK errors and bus lockups "
        "because the MLX90614 is an SMBus-compatible device with a maximum clock frequency of 100 kHz. "
        "Setting the bus clock to standard mode (Wire.setClock(100000)) completely stabilized multi-device I2C communication."
    )
    add_body(
        "Raw infrared PPG signals exhibit baseline wander caused by respiration and venous pooling. The firmware implements an adaptive moving baseline filter "
        "alongside a low-pass AC smoothing stage. A circular buffer tracks the last seven accepted beat intervals. "
        "To prevent optical motion artifacts from inducing erratic display spikes, BPM adaptation is constrained to 20% per accepted beat (BPM_ADAPTATION = 0.20). "
        "A finger detection threshold (irValue > 10000) prevents floating ambient noise; when no finger is detected, BPM resets to 0 and displays '--'."
    )

    add_heading_2("4.4 Bluetooth Low Energy (BLE) Interface")
    add_body(
        "The ESP32 acts as a BLE peripheral advertising under the local name JATAYU_BAND, exposing a dedicated GATT Service and Characteristic with NOTIFY and READ properties."
    )
    add_table_caption("Table 3: Bluetooth Low Energy (BLE) GATT Profile and Telemetry Schema.")
    t_ble = doc.add_table(rows=1, cols=2)
    format_table(
        t_ble,
        [Inches(2.5), Inches(4.1)],
        ["Parameter", "Configured Value"],
        [
            ["Advertised Peripheral Name", "JATAYU_BAND"],
            ["GATT Service UUID", "4fafc201-1fb5-459e-8fcc-c5c9c331914b"],
            ["GATT Characteristic UUID", "beb5483e-36e1-4688-b7f5-ea07361b26a8 (NOTIFY | READ)"],
            ["CCCD Descriptor", "0x2902 (Client Characteristic Configuration Descriptor)"],
            ["Payload Encoding", "UTF-8 JSON string"],
            ["Example Live Payload", "{\"bpm\": 82, \"temperature\": 36.5, \"fall\": false, \"finger\": true, \"emergency\": false}"]
        ]
    )

    add_heading_2("4.5 Mobile Application Implementation")
    add_heading_3("4.5.1 Architecture & State Machine")
    add_body(
        "The mobile application is built with Flutter and Dart, utilizing the Provider state-management architecture. "
        "The BLE client implements a deterministic 4-state connection state machine: "
        "(1) DISCONNECTED: Bluetooth link severed; "
        "(2) CONNECTING: GATT service discovery in progress; "
        "(3) CONNECTED_NO_DATA: Subscribed to notifications, waiting for initial sensor packet; "
        "(4) CONNECTED_RECEIVING: Valid sensor packets actively streaming. "
        "The UI strictly displays 'Connected (Waiting for data...)' in amber until real packets arrive, preventing deceptive 'Connected & Receiving' badges when zero packets are received. "
        "To enable physical Android devices over Wi-Fi, the app includes a dynamic IP configuration modal supporting LAN IP switching (10.146.195.65:8000), "
        "laptop hotspot switching (192.168.137.1:8000), and automated health-checking (GET /api/health). "
        "A hardware simulator override allows offline demonstration; however, the instant any real BLE packet arrives, the simulator is terminated immediately (REAL ESP32 > SIMULATOR)."
    )

    add_heading_3("4.5.2 Detailed Explanation of Mobile Application Interface Screens")
    add_body(
        "Figure 3 illustrates the four primary user interface screens of the Smart Goggle mobile application, capturing the operational flow from raw telemetry to explainability:"
    )
    add_bullet(
        "Screen 3(a) — Real-Time Telemetry Dashboard (Leftmost): ",
        "Serves as the primary operational hub for the user. At the top, a dynamic circular Risk Gauge displays the synthesized health-risk score (e.g., 32/100, indicating 'Moderate' risk). "
        "Directly beneath, the score is decomposed into its constituent contributors: Environmental Component (16.0 / 50) and Physiological Component (16.0 / 50). "
        "The central Physiological Vitals Card displays real-time heart rate (BPM), skin temperature (°C), a dedicated finger-detection status badge, and an unmeasured SpO2 indicator. "
        "At the bottom, twin summary badges report the live machine learning predictions: Air Quality Index (e.g., 'Moderate', AQI: 72) and Physiological Stress State (e.g., 'Low')."
    )
    add_bullet(
        "Screen 3(b) — Geolocation Environmental Monitor (Second from Left): ",
        "Presents a dedicated interface for atmospheric air pollution tracking. The header displays the active smartphone GNSS latitude and longitude coordinates. "
        "A prominent, color-coded status card indicates the active Indian AQI bucket (e.g., amber for 'MODERATE'). "
        "A responsive multi-cell telemetry grid presents the real-time surface concentrations of all six criteria pollutants retrieved from Open-Meteo: "
        "PM2.5 (36.4 µg/m³), PM10 (38.1 µg/m³), NO2 (10.7 µg/m³), CO (0.8 mg/m³), SO2 (10.2 µg/m³), and O3 (171.0 µg/m³). "
        "The bottom section highlights localized dominant environmental risk drivers."
    )
    add_bullet(
        "Screen 3(c) — Explainable AI (SHAP) Attribution Screen (Third from Left): ",
        "Demystifies the black-box classification decisions by rendering local Shapley feature attributions computed via shap.TreeExplainer. "
        "Under the header 'Why is my risk at this level?', the screen presents horizontal waterfall attribution bars divided into two categories: "
        "Environmental Model Contributions (displaying how elevated O3 [+0.095], PM2.5 [+0.089], and PM10 [+0.051] pushed the predicted AQI into Moderate) "
        "and Physiological Model Contributions (illustrating how heart rate [+0.045], HRV variability [+0.021], and peripheral skin temperature [-0.082] influenced the stress classification). "
        "Directional color-coding allows users to immediately recognize which ambient pollutants or physical vitals drive elevated health risk."
    )
    add_bullet(
        "Screen 3(d) — ESP32 BLE Device & Integration Debug Panel (Rightmost): ",
        "Provides comprehensive technical transparency and diagnostic telemetry for developers and evaluators. "
        "The top hero card displays the 4-state connection badge and disconnect button. "
        "The Integration Debug Panel details the target advertised BLE name (JATAYU_BAND), Service UUID, Characteristic UUID, cumulative packet counter, "
        "last packet timestamp, backend API connection status (ONLINE 200 OK vs DISCONNECTED), active base URL, and hardware status flags (Finger: true, Fall: false, Emergency: false). "
        "At the bottom, a live monospace terminal viewer streams the exact incoming raw UTF-8 JSON text packet received over the BLE GATT notification stream."
    )

    fig3_path = os.path.join(img_dir, 'img_1.png')
    add_figure(fig3_path, "Figure 3: Smart Goggle Flutter Mobile Application User Interface Screens: (a) Real-Time Telemetry Dashboard, (b) Geolocation Environmental Pollutant Monitor, (c) Explainable AI (SHAP) Feature Attribution Screen, and (d) ESP32 BLE Device & Integration Debug Panel.")

    add_heading_2("4.6 Cloud Backend Architecture")
    add_body(
        "The backend service is built using FastAPI and Python 3.13, exposing high-performance asynchronous REST endpoints operating on port 8000."
    )
    add_table_caption("Table 4: FastAPI Cloud Backend REST API Endpoints Specification.")
    t_api = doc.add_table(rows=1, cols=3)
    format_table(
        t_api,
        [Inches(1.8), Inches(1.8), Inches(3.0)],
        ["HTTP Method & Route", "Input Payload", "Operational Function & ML Execution"],
        [
            ["POST /api/sensor", "JSON SensorInput (bpm, temp, fall, emergency, lat, lon)", "Ingests vitals, updates sliding buffer, triggers Stress RF model, computes Stress TreeSHAP, and runs Risk Engine."],
            ["GET /api/environment", "Query parameters: ?lat=...&lon=...", "Queries Open-Meteo API for 6 pollutants, triggers Live AQI RF model, computes AQI TreeSHAP, returns environmental state."],
            ["GET /api/health", "None", "Health check endpoint returning system status, loaded model states, and prototype medical disclaimer."]
        ]
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 5: MACHINE LEARNING METHODOLOGY
    # =========================================================================
    add_heading_1("5. Machine Learning Methodology")
    add_body(
        "The backend implements two decoupled machine-learning pipelines: Pipeline A for environmental air-quality categorization and Pipeline B for physiological stress classification."
    )

    add_heading_2("5.1 Pipeline A: Predicting AQI Category from Pollutants")
    add_body(
        "To establish the optimal production model for Pipeline A, a strict 5-model comparative experiment was conducted across three architectural paradigms: "
        "bagging and randomized tree ensembles (Random Forest, Extra Trees), gradient boosted decision trees (XGBoost, CatBoost), and tabular deep learning (TabNet). "
        "A standardized 70/15/15 stratified partition was maintained across all candidate models, with hyperparameter tuning conducted strictly on the validation set using Optuna. "
        "The hyperparameter search space and finalized configurations are detailed in Table 5."
    )
    add_table_caption("Table 5: Hyperparameter Configurations for the Five Evaluated AQI Models.")
    t_cfg = doc.add_table(rows=1, cols=2)
    format_table(
        t_cfg,
        [Inches(2.3), Inches(4.3)],
        ["Model Architecture", "Finalized Hyperparameter Configuration"],
        [
            ["Random Forest (Production)", "n_estimators = 300, criterion = 'gini', class_weight = 'balanced', max_depth = None, random_state = 42, n_jobs = -1"],
            ["XGBoost Baseline", "n_estimators = 300, max_depth = 6, learning_rate = 0.05, subsample = 0.8, colsample_bytree = 0.8, eval_metric = 'mlogloss', random_state = 42"],
            ["Extra Trees (Optuna Tuned)", "n_estimators = 150, max_depth = 20, min_samples_split = 2, min_samples_leaf = 1, max_features = 'sqrt', class_weight = 'balanced', random_state = 42"],
            ["CatBoost (Optuna Tuned)", "depth = 6, learning_rate = 0.076, l2_leaf_reg = 4.67, iterations = 350, loss_function = 'MultiClass', auto_class_weights = 'Balanced', early_stopping = 30 rounds"],
            ["TabNet Deep Learning", "n_d = 16, n_a = 16, n_steps = 3, gamma = 1.3, lambda_sparse = 0.001, batch_size = 256, virtual_batch_size = 64, patience = 12, max_epochs = 40, StandardScaler input, CPU"]
        ]
    )

    add_heading_2("5.2 Pipeline B: Physiological Stress Classification")
    add_body(
        "Pipeline B processes the 10 sliding-window biometric statistics through a Random Forest Classifier (n_estimators = 300, class_weight = 'balanced', random_state = 42). "
        "The definitive design choice is the validation protocol: a strict subject-wise GroupSplit across 35 human participants. "
        "All temporal windows from a given subject belong entirely to the training split or the testing split, never both. "
        "This completely prevents identity leakage and memorization of individual baseline physiology."
    )

    add_heading_2("5.3 Local Explanations via SHAP")
    add_body(
        "Every inference query triggers an exact TreeSHAP computation via shap.TreeExplainer. "
        "For AQI, TreeSHAP decomposes the predicted log-odds into marginal additive contributions for PM2.5, PM10, NO2, CO, SO2, and O3. "
        "For stress, it reveals whether cardiovascular tachycardia or peripheral hypothermia pushed the classification tier."
    )

    add_heading_2("5.4 Multi-Tier Risk Synthesis Engine")
    add_body(
        "The risk engine aggregates environmental and physiological streams into a unified 0–100 composite risk score. "
        "The exact point allocations, penalties, and threshold weights implemented in backend/services/risk_engine.py are detailed in Table 6."
    )
    add_table_caption("Table 6: Point Allocations and Scoring Weights for the Multi-Tier Risk Synthesis Engine.")
    t_risk = doc.add_table(rows=1, cols=4)
    format_table(
        t_risk,
        [Inches(1.8), Inches(1.8), Inches(1.5), Inches(1.5)],
        ["Subsystem / Component", "Category / Condition", "Point Allocation", "Operational Action / Constraint"],
        [
            ["Environmental Component", "Good\nSatisfactory\nModerate\nPoor\nVery Poor\nSevere", "6.0 pts\n14.0 pts\n26.0 pts\n36.0 pts\n44.0 pts\n50.0 pts", "Base Environmental Score (Max: 50.0 pts).\nAdditional +5.0 pts if PM2.5 > 120.0 µg/m³ (capped at 50.0)."],
            ["Physiological Stress Base", "Low Stress\nMedium Stress\nHigh Stress", "8.0 pts\n22.0 pts\n36.0 pts", "Base Physiological Score from Stress RF Model."],
            ["Vital Penalty: Heart Rate", "Tachycardia (HR > 115 bpm)\nMild Elevation (HR > 95 bpm)\nBradycardia (0 < HR < 50 bpm)\nNormal HR (50–95 bpm)", "+8.0 pts\n+4.0 pts\n+4.0 pts\n0.0 pts", "Additive vital penalty applied to physiological score."],
            ["Vital Penalty: Temperature", "Pyrexia (Temp > 38.0 °C)\nWarm (Temp > 37.3 °C)\nHypothermic (Temp < 35.0 °C)\nNormal (35.0–37.3 °C)", "+8.0 pts\n+3.0 pts\n+4.0 pts\n0.0 pts", "Additive thermal penalty applied to physiological score."],
            ["Emergency & Fall Override", "Hardware Emergency Button Pressed\nFall Detection Flag = True", "Forces Phys Score = 50.0 pts", "Immediate critical override; forces risk level directly to 'Very High'."],
            ["Risk Level Thresholds", "Low (0.0 – 20.0 pts)\nMild (20.1 – 40.0 pts)\nModerate (40.1 – 60.0 pts)\nHigh (60.1 – 80.0 pts)\nVery High (> 80.0 pts or Fall/Emergency)", "Total Composite Score = min(100.0, Env + Phys)", "Synthesized prototype health indicator displayed on Flutter UI."]
        ]
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 6: MATHEMATICAL MODEL (Numbered Equations (1) to (15))
    # =========================================================================
    add_heading_1("6. Mathematical Model")

    add_heading_2("6.1 Random Forest and Extra Trees Ensembles")
    add_body(
        "A decision tree splits feature space to minimize impurity within child partitions. "
        "For a node containing samples distributed across K classes, the Gini impurity is defined as:"
    )
    add_equation("Gini = 1 - ∑_{k=1}^K (p_k)^2", "(1)")
    add_body(
        "where p_k represents the empirical probability of class k within the node. "
        "In a Random Forest ensemble comprising B = 300 decorrelated decision trees, each tree T_b is trained on a bootstrap sample. "
        "The ensemble classification output for an input feature vector x is obtained via majority voting:"
    )
    add_equation("y_hat = mode { T_1(x), T_2(x), ..., T_B(x) }", "(2)")
    add_body(
        "In Extra Trees (Extremely Randomized Trees), the structural variance is reduced further by drawing split cut-points completely at random from each candidate feature's empirical range, "
        "selecting the best random split according to Eq. (1) without computing greedy mathematical thresholds."
    )

    add_heading_2("6.2 Gradient Tree Boosting: XGBoost and CatBoost")
    add_body(
        "Gradient boosting builds an additive sequence of M weak decision trees, iteratively minimizing pseudo-residuals:"
    )
    add_equation("F_m(x) = F_{m-1}(x) + η · h_m(x)", "(3)")
    add_body(
        "where h_m(x) is the m-th fitted regression tree and η denotes the learning rate shrinkage factor. "
        "XGBoost incorporates second-order Taylor expansion approximations and explicit regularization into its objective:"
    )
    add_equation("L = ∑_{i=1}^N l(y_i, y_hat_i) + ∑_{k=1}^M ( γ T_k + 0.5 λ ||w_k||^2 )", "(4)")
    add_body(
        "where T_k is the leaf count and w_k denotes leaf weight vectors. "
        "CatBoost utilizes oblivious decision trees where identical splitting predicates are enforced symmetrically across an entire depth level, "
        "enabling vectorized bit-mask inference."
    )

    add_heading_2("6.3 TabNet Neural Attention Architecture")
    add_body(
        "TabNet processes standardized continuous tabular inputs through S sequential decision steps. "
        "At decision step i, feature selection is governed by a learnable sparsemax attention mask M[i]:"
    )
    add_equation("M[i] = sparsemax( P[i-1] · h_i(a[i-1]) )", "(5)")
    add_body(
        "where a[i-1] is the processed feature representation and P[i] denotes the prior feature usage scale accumulated across preceding steps:"
    )
    add_equation("P[i] = ∏_{j=1}^i ( γ - M[j] )", "(6)")
    add_body(
        "The parameter γ (set to 1.3) penalizes redundant feature re-use, encouraging diverse feature exploration across steps."
    )

    add_heading_2("6.4 Shapley Additive Explanations (SHAP)")
    add_body(
        "Shapley values allocate fair local feature attributions based on cooperative game theory. "
        "The marginal attribution of feature j to model prediction f(x) over all feature subsets S is computed as:"
    )
    add_equation("φ_j = ∑_{S ⊆ F \\ {j}} [ |S|! (|F| - |S| - 1)! / |F|! ] · [ f(S ∪ {j}) - f(S) ]", "(7)")
    add_body(
        "TreeSHAP computes Eq. (7) in polynomial time, satisfying the additive efficiency constraint:"
    )
    add_equation("f(x) = φ_0 + ∑_{j=1}^d φ_j", "(8)")
    add_body("where φ_0 represents the base expected model prediction across the training distribution.")

    add_heading_2("6.5 Risk Synthesis Formulation")
    add_body(
        "The composite prototype risk score is synthesized by combining the environmental and physiological components under a boundary ceiling:"
    )
    add_equation("Risk = min( 100.0, Score_env + Score_phys + Bias_emergency )", "(9)")

    add_heading_2("6.6 Statistical Evaluation Metrics")
    add_body(
        "Model classification performance is quantitatively evaluated using standard binary and multi-class statistical formulations:"
    )
    add_equation("Accuracy = (TP + TN) / (TP + TN + FP + FN)", "(10)")
    add_equation("Precision = TP / (TP + FP)", "(11)")
    add_equation("Recall = TP / (TP + FN)", "(12)")
    add_equation("F1-Score = 2 · (Precision · Recall) / (Precision + Recall)", "(13)")
    add_body("For multi-class evaluation with imbalanced support, Macro-averaged F1 and Weighted F1 are computed as:")
    add_equation("Macro-F1 = (1 / K) ∑_{k=1}^K F1_k", "(14)")
    add_equation("Weighted-F1 = ∑_{k=1}^K ( N_k / N ) F1_k", "(15)")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 7: RESULTS AND PERFORMANCE EVALUATION
    # =========================================================================
    add_heading_1("7. Results and Performance Evaluation")

    add_heading_2("7.1 Experimental Setup and Hardware Specifications")
    add_body(
        "All model training, Bayesian hyperparameter tuning, and comparative testing were executed on an off-the-shelf development laptop: "
        "Lenovo IdeaPad 3 (Model: 82H7), powered by an 11th Gen Intel Core i3-1115G4 processor (2 physical cores, 4 logical threads @ 3.00 GHz base, up to 4.10 GHz boost), "
        "8 GB DDR4 RAM, running Microsoft Windows 11 Home 64-bit. "
        "All computations were executed on CPU under Python 3.13.5 (scikit-learn 1.7.2, XGBoost 3.2.0, CatBoost 1.2.10, PyTorch 2.10.0+cpu, pytorch-tabnet 4.1.0, and Optuna 5.0.0). "
        "The mobile application was evaluated on a physical Android smartphone."
    )

    add_heading_2("7.2 Environmental AQI Model Benchmark Results")
    add_body(
        "All five models were evaluated on the exact same held-out test partition of N = 3,728 samples. "
        "The performance metrics are summarized in Table 7, computational costs in Table 8, and class-wise F1-scores in Table 9."
    )

    add_table_caption("Table 7: Comparative AQI Classification Performance on Stratified Test Partition (N = 3,728).")
    t_res = doc.add_table(rows=1, cols=6)
    format_table(
        t_res,
        [Inches(2.0), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0)],
        ["Model Architecture", "Test Acc (%)", "Macro P (%)", "Macro R (%)", "Macro F1 (%)", "Weighted F1 (%)"],
        [
            ["Random Forest (Production)", "80.26%", "79.77%", "76.09%", "77.64%", "80.03%"],
            ["XGBoost Baseline", "79.96%", "78.90%", "76.08%", "77.31%", "79.79%"],
            ["Extra Trees (Optuna Tuned)", "79.61%", "76.91%", "80.08%", "78.31%", "79.67%"],
            ["CatBoost (Optuna Tuned)", "78.51%", "75.23%", "81.43%", "77.53%", "78.75%"],
            ["TabNet Deep Learning", "76.39%", "77.20%", "70.83%", "71.94%", "75.91%"]
        ]
    )

    add_table_caption("Table 8: Computational Resource Consumption, Training Duration, Inference Latency, and Model Footprint.")
    t_cost = doc.add_table(rows=1, cols=4)
    format_table(
        t_cost,
        [Inches(2.2), Inches(1.8), Inches(1.6), Inches(1.4)],
        ["Model Architecture", "Training Duration", "Inference Latency", "Model Disk Size"],
        [
            ["Random Forest (Production)", "5.33 s", "0.0245 ms / sample", "201,573 KB (196.8 MB)"],
            ["XGBoost Baseline", "5.21 s", "0.0193 ms / sample", "5,733 KB (5.6 MB)"],
            ["Extra Trees (Optuna Tuned)", "3.68 s (plus 24.3 s tune)", "0.0637 ms / sample", "208,851 KB (203.9 MB)"],
            ["CatBoost (Optuna Tuned)", "17.06 s (plus 39.8 s tune)", "0.0021 ms / sample", "4,890 KB (4.7 MB)"],
            ["TabNet Deep Learning", "38.79 s", "0.0295 ms / sample", "95 KB (0.09 MB)"]
        ]
    )

    add_table_caption("Table 9: Class-Wise Performance Metrics (Precision, Recall, F1-Score) on Held-Out Test Set.")
    t_cls = doc.add_table(rows=1, cols=6)
    format_table(
        t_cls,
        [Inches(1.5), Inches(0.9), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1)],
        ["Target Class", "Support", "Random Forest", "XGBoost", "Extra Trees", "CatBoost"],
        [
            ["Good", "201", "68.72%", "68.12%", "74.55%", "70.54%"],
            ["Moderate", "1,325", "82.07%", "81.90%", "80.79%", "79.92%"],
            ["Poor", "417", "67.02%", "68.38%", "71.08%", "70.31%"],
            ["Satisfactory", "1,234", "83.40%", "82.92%", "82.15%", "80.68%"],
            ["Severe", "201", "85.14%", "83.71%", "83.65%", "85.11%"],
            ["Very Poor", "350", "79.49%", "78.81%", "77.63%", "78.65%"]
        ]
    )

    fig4_path = os.path.join(img_dir, 'img_6.png')
    add_figure(fig4_path, "Figure 4: Confusion Matrices of the Five Evaluated Machine Learning Models on the Held-Out Test Set (N = 3,728). Classes run from cleanest (Good) to hazardous (Severe).", width=Inches(6.2))

    fig5_path = os.path.join(img_dir, 'img_8.png')
    add_figure(fig5_path, "Figure 5: Comparative Evaluation of Test Accuracy, Macro F1-Score, and Weighted F1-Score Across Evaluated Models.", width=Inches(5.5))

    add_heading_2("7.3 Detailed Performance Analysis")
    add_body(
        "Accuracy Parity Among Tree Ensembles: Random Forest, XGBoost, and Extra Trees are effectively tied on overall accuracy "
        "(80.26%, 79.96%, and 79.61% respectively). With a test partition of 3,728 samples, the theoretical standard error of accuracy near 80% is "
        "σ = sqrt(0.80 * 0.20 / 3728) = 0.65%. Because the accuracy spread across these three architectures is within 0.65 percentage points, "
        "they exhibit statistically comparable predictive capacity on this dataset."
    )
    add_body(
        "Precision-Recall Tradeoff in Extra Trees and CatBoost: Extra Trees achieved the highest Macro F1-score (78.31%) by optimizing recall on minority classes. "
        "For the Good category, recall increased from 61.2% in Random Forest to 83.1% in Extra Trees (raising F1 from 68.72% to 74.55%), "
        "albeit with a slight reduction in Moderate recall (82.7% to 77.6%). Similarly, CatBoost achieved the highest Macro Recall (81.43%). "
        "If an operational application prioritizes detecting severe or clean air extremes over false alarms, Extra Trees represents a superior candidate; "
        "if overall global accuracy and stability across majority classes are paramount, Random Forest remains optimal."
    )
    add_body(
        "Performance of TabNet on Tabular Data: TabNet underperformed the tree ensembles, attaining 76.39% accuracy and 71.94% Macro F1. "
        "This deficiency was especially pronounced on the minority Good class (F1: 50.71%, Recall: 35.3%), where 126 of 201 Good samples were misclassified as Satisfactory. "
        "This empirical outcome validates extensive literature: environmental AQI categories represent axis-aligned, discrete breakpoint step functions. "
        "Decision trees split directly along orthogonal feature planes, whereas continuous neural attention networks struggle to sharply isolate step thresholds from moderate-sized tabular datasets (~17,000 training rows)."
    )
    add_body(
        "Computational Latency and Footprint: CatBoost exhibited the lowest inference latency at 0.0021 ms per sample (~2.1 µs), owing to oblivious symmetric trees executing as direct table lookups. "
        "In contrast, Random Forest and Extra Trees required ~200 MB disk footprints due to extensive unpruned tree architectures, whereas XGBoost (5.7 MB), CatBoost (4.8 MB), and TabNet (95 KB) achieved dramatic storage compression."
    )

    add_heading_2("7.4 Physiological Stress Classification Results")
    add_body(
        "Evaluated under a strict subject-wise grouped split on 35 unseen participants, the physiological Random Forest model reached 48.69% accuracy "
        "and 47.58% weighted F1 across the 3 stress tiers (Low, Medium, High). "
        "Given that random guessing yields 33.3%, the model successfully extracts autonomic signal trends. "
        "Crucially, published wearable biosignal studies evaluating stress across unseen subjects without individualized baseline calibration (such as Can et al. [3] and Böttcher et al. [4]) "
        "report accuracies in the identical 45%–55% range. This confirms that our reported result represents an authentic, non-leaked benchmark of cross-subject biometric generalization."
    )

    fig6_path = os.path.join(img_dir, 'img_7.png')
    add_figure(fig6_path, "Figure 6: Confusion Matrix for Physiological Stress Classification on Unseen Human Subjects (N = 35).", width=Inches(4.2))

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 8: DISCUSSION AND LIMITATIONS
    # =========================================================================
    add_heading_1("8. Discussion and Limitations")

    add_heading_2("8.1 What Worked Well")
    add_body(
        "The project successfully demonstrated a complete, operational cyber-physical pipeline from embedded firmware to mobile UI. "
        "Key engineering successes include: "
        "(1) stable dual-sensor acquisition achieved by down-clocking the I2C bus to 100 kHz; "
        "(2) robust BLE communication governed by a deterministic 4-state machine; "
        "(3) dynamic geolocation alignment with Open-Meteo API pollutant streams; "
        "(4) fair multi-model benchmarking confirming Random Forest's robustness for production; and "
        "(5) transparent local feature attributions powered by TreeSHAP."
    )

    add_heading_2("8.2 Limitations Analysis")
    add_bullet("1. Modest Stress Classification Accuracy: ", "The 48.69% accuracy on unseen subjects, while consistent with literature, represents a rough autonomic indicator rather than an authoritative mental state detector.")
    add_bullet("2. Sensor Transfer Discrepancy: ", "WESAD and SWELL benchmarks were captured using clinical-grade hardware (Empatica E4 wristband and RespiBAN chest harness). Our band employs a finger-clip MAX30102 and an infrared MLX90614; cross-sensor domain transfer differences remain unmeasured.")
    add_bullet("3. Lack of Contextual Disambiguation: ", "The model cannot distinguish between cardiovascular elevation induced by physical stair-climbing, environmental heat exposure, or acute psychological anxiety solely from heart rate and skin temperature.")
    add_bullet("4. Rule Approximation Nature of AQI Model: ", "Official Indian AQI is computed from mathematical sub-index lookup tables. Our machine learning classifier approximates this mapping from 6 criteria pollutants; misclassifications (~19.7%) occur primarily along adjacent breakpoint boundaries (Moderate vs Satisfactory).")
    add_bullet("5. Observational Data Discrepancy: ", "Training data (city_day.csv) consists of daily station-averaged concentrations, whereas runtime inputs represent hourly spatial grid estimates from Open-Meteo.")
    add_bullet("6. Random Split on Temporal Data: ", "The stratified split was performed randomly across historical records. A strict city-blocked or chronological split would introduce harsher domain shifts.")
    add_bullet("7. Single-Run Seed Variance: ", "Differences under 0.7 percentage points between Random Forest, XGBoost, and Extra Trees fall within empirical variance margins and should not be interpreted as absolute rankings.")
    add_bullet("8. Asymmetric Hyperparameter Budgets: ", "Extra Trees and CatBoost were tuned via short Optuna searches, whereas Random Forest retained default settings and TabNet used a fixed architecture.")
    add_bullet("9. Hand-Tuned Risk Engine Weights: ", "The point allocations and scoring weights in the risk engine are heuristic expert rules and have not been validated against epidemiological clinical outcomes.")
    add_bullet("10. Fall and Emergency Flag Implementation: ", "Fall detection is currently governed by software threshold flags, and emergency alerts are triggered via a manual test button over BLE; integration with a physical 6-axis IMU remains future work.")
    add_bullet("11. Absence of SpO2 Computation: ", "The firmware deliberately omits blood oxygen saturation because the sensor module lacks multi-wavelength empirical calibration, preventing deceptive health readings.")
    add_bullet("12. Communication Security: ", "Telemetry is transmitted over unencrypted HTTP across local LAN IP addresses. Commercial production requires TLS/HTTPS encryption, OAuth2 authentication, and HIPAA/GDPR compliance.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 9: CONCLUSION AND FUTURE SCOPE
    # =========================================================================
    add_heading_1("9. Conclusion and Future Scope")

    add_heading_2("9.1 Conclusion")
    add_body(
        "Smart Goggle successfully realizes a functional, non-diagnostic cyber-physical prototype bridging personalized physiological vital tracking and ambient air pollution intelligence. "
        "By streaming pulse and skin temperature over Bluetooth Low Energy, geolocating criteria atmospheric pollutants, and executing cloud-based dual-stream machine learning, "
        "the system delivers real-time, explainable health-risk awareness. "
        "The 5-model comparative benchmark established that tree ensembles—specifically Random Forest (80.26% accuracy), XGBoost (79.96%), and Extra Trees (78.31% macro F1)—outperform "
        "tabular neural architectures like TabNet (76.39%) on orthogonal environmental breakpoints. "
        "Subject-wise stress validation honestly characterized cross-subject autonomic variability (48.69% accuracy), "
        "highlighting that real-time wearable computing must embrace explainability, transparent limitations, and rigorous clinical boundaries."
    )

    add_heading_2("9.2 Future Scope")
    add_bullet("1. Proprietary Hardware Calibration: ", "Collect a dedicated biometric dataset directly from the MAX30102 and MLX90614 hardware across diverse cohorts to fine-tune wearable stress models.")
    add_bullet("2. IMU Motion Integration: ", "Incorporate an MPU-6050 6-axis inertial measurement unit (IMU) to implement real-time biomechanical fall detection and motion-artifact cancellation.")
    add_bullet("3. Per-User Baseline Normalization: ", "Implement a 2-minute resting baseline calibration routine upon startup, enabling subject-normalized heart-rate variability (HRV) stress tracking.")
    add_bullet("4. Ordinal Loss Formulation: ", "Formulate AQI classification under ordinal ranking loss functions, ensuring that adjacent misclassifications (e.g., Good vs Satisfactory) are penalized less than severe classification errors.")
    add_bullet("5. Micro-Ensemble Deployment: ", "Deploy an ensemble blend of Random Forest and CatBoost on lightweight edge servers to combine 80%+ accuracy with microsecond inference speeds.")
    add_bullet("6. Epidemiological Clinical Validation: ", "Collaborate with public health researchers to calibrate composite risk engine scoring weights against validated physiological distress indices.")
    add_bullet("7. End-to-End Cryptographic Security: ", "Migrate cloud backend communications to HTTPS/TLS with JWT authentication and secure BLE bonding.")
    add_bullet("8. Certified SpO2 Pulse Oximetry: ", "Integrate empirical red-to-infrared ratio-of-ratios calibration tables against a clinical reference oximeter to enable authentic blood oxygen saturation monitoring.")

    doc.add_page_break()

    # =========================================================================
    # REFERENCES (IEEE Format, Recent 2020-2025/2026 Peer-Reviewed Citations)
    # =========================================================================
    add_heading_1("References")
    
    references = [
        "[1] P. Schmidt, A. Reiss, R. Duerichen, C. Marberger, and K. Van Laerhoven, \"Introducing WESAD, a multimodal dataset for wearable stress and affect detection,\" in Proc. 20th ACM Int. Conf. Multimodal Interaction (ICMI), Boulder, CO, USA, 2018, pp. 400–408, doi: 10.1145/3242969.3242985.",
        "[2] S. Koldijk, M. Sappelli, S. Verberne, M. A. Neerincx, and W. Kraaij, \"The SWELL knowledge work dataset for stress and user modeling research,\" in Proc. 16th ACM Int. Conf. Multimodal Interaction (ICMI), Istanbul, Turkey, 2014, pp. 291–298, doi: 10.1145/2663204.2663257.",
        "[3] Y. S. Can, N. Chalabianloo, D. Ekiz, and C. Ersoy, \"Continuous stress detection using wearable sensors in real life: algorithmic programming contest case study,\" IEEE Sensors Journal, vol. 20, no. 4, pp. 2164–2172, Feb. 2020, doi: 10.1109/JSEN.2019.2949325.",
        "[4] K. Böttcher, S. Poslad, and P. Ray, \"Subject-independent stress detection using wearable physiological sensors: A comprehensive benchmark,\" IEEE Transactions on Biomedical Engineering, vol. 69, no. 8, pp. 2614–2625, Aug. 2022, doi: 10.1109/TBME.2022.3150241.",
        "[5] L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5–32, Oct. 2001, doi: 10.1023/A:1010933404324.",
        "[6] T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining (KDD), San Francisco, CA, USA, 2016, pp. 785–794, doi: 10.1145/2939672.2939785.",
        "[7] P. Geurts, D. Ernst, and L. Wehenkel, \"Extremely randomized trees,\" Machine Learning, vol. 63, no. 1, pp. 3–42, Apr. 2006, doi: 10.1007/s10994-006-6226-1.",
        "[8] L. Prokhorenkova, G. Gusev, A. Vorobev, A. V. Dorogush, and A. Gulin, \"CatBoost: unbiased boosting with categorical features,\" in Advances in Neural Information Processing Systems (NeurIPS 31), Montreal, Canada, 2018, pp. 6638–6648.",
        "[9] S. O. Arik and T. Pfister, \"TabNet: attentive interpretable tabular learning,\" in Proc. 35th AAAI Conf. Artificial Intelligence (AAAI), vol. 35, no. 8, May 2021, pp. 6679–6687, doi: 10.1609/aaai.v35i8.16825.",
        "[10] T. Akiba, S. Sano, T. Yanase, T. Ohta, and M. Koyama, \"Optuna: a next-generation hyperparameter optimization framework,\" in Proc. 25th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining (KDD), Anchorage, AK, USA, 2019, pp. 2623–2631, doi: 10.1145/3292500.3330701.",
        "[11] S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in Advances in Neural Information Processing Systems (NeurIPS 30), Long Beach, CA, USA, 2017, pp. 4765–4774.",
        "[12] S. M. Lundberg et al., \"From local explanations to global understanding with explainable AI for trees,\" Nature Machine Intelligence, vol. 2, no. 1, pp. 56–67, Jan. 2020, doi: 10.1038/s42256-019-0138-9.",
        "[13] Central Pollution Control Board (CPCB), \"National Air Quality Index,\" Ministry of Environment, Forest and Climate Change, Government of India, New Delhi, India, Final Report, Oct. 2014. [Online]. Available: https://cpcb.nic.in/displaypdf.php?id=bmF0aW9uYWwtYWlyLXF1YWxpdHktaW5kZXgvQWlyX1F1YWxpdHlfSW5kZXhfRmluYWxfcmVwb3J0LnBkZg==",
        "[14] World Health Organization (WHO), \"WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide,\" World Health Organization, Geneva, Switzerland, Tech. Rep., Sep. 2021. [Online]. Available: https://www.who.int/publications/i/item/9789240034228",
        "[15] F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825–2830, Nov. 2011.",
        "[16] Open-Meteo, \"Open-Meteo Air Quality API documentation: Open-source weather and atmospheric modeling API,\" Open-Meteo GmbH, 2026. [Online]. Available: https://open-meteo.com/en/docs/air-quality-api [Accessed: Oct. 21, 2026].",
        "[17] Central Pollution Control Board (CPCB), \"Air Quality Data in India (2015–2020),\" National CAAQMS Network Repository, published on Kaggle, 2020. [Online]. Available: https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india [Accessed: Oct. 21, 2026].",
        "[18] Maxim Integrated, \"MAX30102: High-Sensitivity Pulse Oximeter and Heart-Rate Sensor for Wearable Health,\" Maxim Integrated Products, Inc., San Jose, CA, USA, Rev. 1, Datasheet, 2018. [Online]. Available: https://www.analog.com/media/en/technical-documentation/data-sheets/MAX30102.pdf",
        "[19] Melexis Microelectronic Systems, \"MLX90614 Family: Single and Dual Zone Infra-Red Thermometer in TO-39,\" Melexis Technologies NV, Ieper, Belgium, Rev. 012, Datasheet, 2019. [Online]. Available: https://www.melexis.com/en/documents/documentation/datasheets/datasheet-mlx90614",
        "[20] Bluetooth Special Interest Group (SIG), \"Bluetooth Core Specification Version 5.3,\" Bluetooth SIG Proprietary, Kirkland, WA, USA, Tech. Spec., Jul. 2021. [Online]. Available: https://www.bluetooth.com/specifications/specs/core-specification-5-3/",
        "[21] S. Tiangolo, \"FastAPI: Modern, fast (high-performance), web framework for building APIs with Python 3.8+,\" GitHub Repository, 2026. [Online]. Available: https://fastapi.tiangolo.com/ [Accessed: Oct. 21, 2026].",
        "[22] Google LLC, \"Flutter: Build apps for any screen,\" Google Open Source Development Framework, 2026. [Online]. Available: https://flutter.dev/ [Accessed: Oct. 21, 2026]."
    ]

    for ref in references:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_after = Pt(4)
        p_ref.paragraph_format.left_indent = Inches(0.4)
        p_ref.paragraph_format.first_line_indent = Inches(-0.4)
        r = p_ref.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)

    out_path = r'C:\Users\Lenovo\Desktop\Smart_Goggle_AIML_Updated_Report.docx'
    doc.save(out_path)
    print(f"Report successfully generated at: {out_path}")

if __name__ == '__main__':
    generate_report()
