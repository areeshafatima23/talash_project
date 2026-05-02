import streamlit as st
import tempfile, os, json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from loader import extract_text_from_pdf, load_cvs_from_folder
from parser import extract_full_profile
from milestone1_pipeline import run_pipeline as run_m1_pipeline
from milestone2_pipeline import run_pipeline as run_m2_pipeline
from milestone3_pipeline import (
    run_pipeline as run_m3_pipeline,
    compute_final_score,
    score_education, score_research, score_topic_diversity,
    score_collaboration, score_books, score_patents,
    score_skills, score_experience,
)

st.set_page_config(page_title="TALASH", layout="wide")
st.title("TALASH")
st.caption("Talent Acquisition & Learning Automation for Smart Hiring")

mode = st.sidebar.radio(
    "Mode",
    [
        "Upload Single CV",
        "Process CVs Folder (Milestone 1)",
        "Milestone 2: Analysis Pipeline",
        "Milestone 3: Comprehensive Analysis",
    ],
)


# MODE 1 — Single CV Upload
if mode == "Upload Single CV":
    st.header("Upload a CV")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with st.spinner("Reading PDF..."):
            text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)

        with st.spinner("Analyzing CV with AI..."):
            profile = extract_full_profile(text)

        st.subheader("Personal Info")
        st.write(f"**Name:** {profile.get('name', 'N/A')}")
        st.write(f"**Email:** {profile.get('email', 'N/A')}")
        st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
        st.write(f"**Address:** {profile.get('address', 'N/A')}")

        st.subheader("Skills")
        st.write(", ".join(profile.get("skills", [])) or "No skills found")

        st.subheader("Education")
        if profile.get("education"):
            st.dataframe(pd.DataFrame(profile["education"]), use_container_width=True)

        st.subheader("Experience")
        if profile.get("experience"):
            st.dataframe(pd.DataFrame(profile["experience"]), use_container_width=True)

        st.subheader("Books")
        if profile.get("books"):
            st.dataframe(pd.DataFrame(profile["books"]), use_container_width=True)
        else:
            st.write("No books found.")

        st.subheader("Patents")
        if profile.get("patents"):
            st.dataframe(pd.DataFrame(profile["patents"]), use_container_width=True)
        else:
            st.write("No patents found.")

        st.subheader("Download JSON / CSV")
        json_filename = uploaded_file.name.replace(".pdf", "_profile.json")
        st.download_button(
            "Download JSON",
            json.dumps(profile, indent=2),
            json_filename,
            mime="application/json",
        )

        flat_csv = pd.DataFrame([{
            "file_name":  uploaded_file.name,
            "name":       profile.get("name",    ""),
            "email":      profile.get("email",   ""),
            "phone":      profile.get("phone",   ""),
            "address":    profile.get("address", ""),
            "education":  json.dumps(profile.get("education",  [])),
            "experience": json.dumps(profile.get("experience", [])),
            "skills":     ", ".join(profile.get("skills", [])),
            "books":      json.dumps(profile.get("books",   [])),
            "patents":    json.dumps(profile.get("patents", [])),
        }]).to_csv(index=False)

        st.download_button(
            "Download CSV",
            flat_csv,
            uploaded_file.name.replace(".pdf", "_profile.csv"),
            "text/csv",
        )


# MODE 2 — Milestone 1 Folder Pipeline 
elif mode == "Process CVs Folder (Milestone 1)":
    st.header("Process All CVs from Folder (Milestone 1)")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_csv = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")

    if st.button("Run Milestone 1 Pipeline"):
        with st.spinner("Processing CVs..."):
            rows = run_m1_pipeline(cvs_folder, output_csv)
        st.session_state["m1_rows"] = rows

    rows = st.session_state.get("m1_rows")
    if rows:
        st.success(f"Processed {len(rows)} CV(s)!")
        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df[["file_name", "name", "email", "phone", "skills"]], use_container_width=True)
        with open(output_csv, "rb") as f:
            st.download_button("Download Full CSV", f, "milestone1_output.csv", "text/csv")
    elif rows is not None:
        st.warning("No CVs found in the folder.")


# MODE 3 — Milestone 2 Analysis Pipeline 
elif mode == "Milestone 2: Analysis Pipeline":
    st.header("Milestone 2: CV Analysis & Missing Info Detection")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone2")

    if st.button("Run Milestone 2 Pipeline"):
        with st.spinner("Processing CVs and performing analysis..."):
            run_m2_pipeline(cvs_folder, output_dir)
        st.session_state["m2_done"] = True
        st.session_state["m2_output_dir"] = output_dir

    if st.session_state.get("m2_done"):
        saved_output_dir = st.session_state.get("m2_output_dir", output_dir)
        st.success(f"Milestone 2 processing completed! Saved in {saved_output_dir}")

        def safe_read(path):
            if os.path.exists(path) and os.path.getsize(path) > 0:
                try:
                    return pd.read_csv(path)
                except:
                    return pd.DataFrame()
            return pd.DataFrame()

        for csv_file in ["personal_info.csv", "education.csv", "experience.csv",
                         "skills.csv", "publications.csv", "missing_info.csv", "draft_emails.csv"]:
            path = os.path.join(saved_output_dir, csv_file)
            df   = safe_read(path)
            st.subheader(csv_file.replace("_", " ").replace(".csv", "").title())
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data in {csv_file}")

        edu_df = safe_read(os.path.join(saved_output_dir, "education.csv"))
        if not edu_df.empty:
            fig = px.histogram(edu_df, x="degree", title="Education Degree Distribution")
            st.plotly_chart(fig, use_container_width=True)
            degree_counts = edu_df["degree"].value_counts().reset_index()
            degree_counts.columns = ["degree", "count"]
            st.plotly_chart(px.pie(degree_counts, names="degree", values="count",
                                   title="Degree Share"), use_container_width=True)

        skills_df = safe_read(os.path.join(saved_output_dir, "skills.csv"))
        if not skills_df.empty:
            top = skills_df["skill"].value_counts().reset_index()
            top.columns = ["skill", "count"]
            st.plotly_chart(px.bar(top.head(20), x="skill", y="count", title="Top 20 Skills"),
                            use_container_width=True)

        pub_df = safe_read(os.path.join(saved_output_dir, "publications.csv"))
        if not pub_df.empty:
            pub_counts = pub_df["file_name"].value_counts().reset_index()
            pub_counts.columns = ["candidate", "num_publications"]
            st.plotly_chart(px.bar(pub_counts, x="candidate", y="num_publications",
                                   title="Publications per Candidate"), use_container_width=True)

        missing_df = safe_read(os.path.join(saved_output_dir, "missing_info.csv"))
        if not missing_df.empty:
            missing_df["missing_count"] = missing_df["missing_fields"].apply(
                lambda x: len(str(x).split(",")))
            st.subheader("Missing Information Summary")
            st.write(f"Total CVs with missing info: {len(missing_df)}")
            st.plotly_chart(px.pie(missing_df, names="file_name", values="missing_count",
                                   title="Missing Info per CV"), use_container_width=True)


# MODE 4 — Milestone 3 Comprehensive Analysis 
elif mode == "Milestone 3: Comprehensive Analysis":
    st.header("Milestone 3: Educational, Research & Innovation Profile Analysis")
    st.info("Place PDF CVs in the `cvs/` folder, then click Run.")

    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_dir = os.path.join(os.path.dirname(__file__), "../output/milestone3")

    if st.button("Run Milestone 3 Pipeline"):
        with st.spinner("Running full analysis — this may take a few minutes per CV..."):
            (analysis_results, global_edu, global_journals, global_confs,
             global_topic_rows, global_coauthor_rows,
             global_book_rows, global_patent_rows,
             global_skills_rows, global_exp_rows,
             global_supervision_rows, global_skill_align_rows,
             global_timeline_rows, global_summaries) = run_m3_pipeline(cvs_folder, output_dir)

        
        st.session_state["m3_done"]             = True
        st.session_state["m3_output_dir"]       = output_dir
        st.session_state["m3_analysis_results"] = analysis_results
        st.session_state["m3_global_edu"]       = global_edu
        st.session_state["m3_global_journals"]  = global_journals
        st.session_state["m3_global_confs"]     = global_confs
        st.session_state["m3_global_topic_rows"]    = global_topic_rows
        st.session_state["m3_global_coauthor_rows"] = global_coauthor_rows
        st.session_state["m3_global_book_rows"]     = global_book_rows
        st.session_state["m3_global_patent_rows"]   = global_patent_rows
        st.session_state["m3_global_skills_rows"]   = global_skills_rows
        st.session_state["m3_global_exp_rows"]      = global_exp_rows
        st.session_state["m3_global_supervision_rows"]  = global_supervision_rows
        st.session_state["m3_global_skill_align_rows"]  = global_skill_align_rows
        st.session_state["m3_global_timeline_rows"]     = global_timeline_rows
        st.session_state["m3_global_summaries"]         = global_summaries

   
    if not st.session_state.get("m3_done"):
        st.stop()

    # Restore from session_state
    output_dir       = st.session_state["m3_output_dir"]
    analysis_results = st.session_state["m3_analysis_results"]
    global_edu       = st.session_state["m3_global_edu"]
    global_journals  = st.session_state["m3_global_journals"]
    global_confs     = st.session_state["m3_global_confs"]
    global_topic_rows    = st.session_state["m3_global_topic_rows"]
    global_coauthor_rows = st.session_state["m3_global_coauthor_rows"]
    global_book_rows     = st.session_state["m3_global_book_rows"]
    global_patent_rows   = st.session_state["m3_global_patent_rows"]
    global_skills_rows   = st.session_state["m3_global_skills_rows"]
    global_exp_rows      = st.session_state["m3_global_exp_rows"]
    global_supervision_rows  = st.session_state["m3_global_supervision_rows"]
    global_skill_align_rows  = st.session_state["m3_global_skill_align_rows"]
    global_timeline_rows     = st.session_state["m3_global_timeline_rows"]
    global_summaries         = st.session_state["m3_global_summaries"]

    st.success("Milestone 3 analysis complete!")

    def safe_df(data):
        return pd.DataFrame(data) if data else pd.DataFrame()

    ar_df   = safe_df(analysis_results)
    edu_df  = safe_df(global_edu)
    j_df    = safe_df(global_journals)
    c_df    = safe_df(global_confs)
    t_df    = safe_df(global_topic_rows)
    ca_df   = safe_df(global_coauthor_rows)
    bk_df   = safe_df(global_book_rows)
    pt_df   = safe_df(global_patent_rows)
    sk_df   = safe_df(global_skills_rows)
    ex_df   = safe_df(global_exp_rows)
    sup_df  = safe_df(global_supervision_rows)
    sal_df  = safe_df(global_skill_align_rows)
    tl_df   = safe_df(global_timeline_rows)
    sum_df  = safe_df(global_summaries)

    #  13 Tabs 
    (tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9,
     tab10, tab11, tab12, tab13) = st.tabs([
        " Overall Analysis",
        " Education",
        " Research (Journals & Conf)",
        " Topic Variability",
        " Co-Author Analysis",
        " Books & Patents",
        " Skills Analysis",
        " Experience Analysis",
        " Supervision",
        " Skill Alignment",
        " Timeline Consistency",
        " Candidate Summaries",
        " Candidate Ranking",
    ])

    # TAB 1: Overall 
    with tab1:
        st.subheader("Candidate Summary Table")
        if not ar_df.empty:
            display_cols = [c for c in [
                "candidate_name", "highest_qualification", "academic_progression",
                "total_publications", "dominant_research_topic", "research_variability_label",
                "total_unique_coauthors", "total_books", "total_patents",
                "unique_skills", "experience_years", "career_progression",
                "total_supervised", "timeline_issues", "timeline_warnings",
            ] if c in ar_df.columns]
            st.dataframe(ar_df[display_cols], use_container_width=True)

            if "total_publications" in ar_df.columns and "candidate_name" in ar_df.columns:
                fig = px.bar(ar_df, x="candidate_name", y="total_publications",
                             title="Total Publications per Candidate",
                             labels={"candidate_name": "Candidate", "total_publications": "Publications"},
                             color="candidate_name")
                st.plotly_chart(fig, use_container_width=True)

            if "total_books" in ar_df.columns and "total_patents" in ar_df.columns:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(name="Books",   x=ar_df["candidate_name"], y=ar_df["total_books"]))
                fig2.add_trace(go.Bar(name="Patents", x=ar_df["candidate_name"], y=ar_df["total_patents"]))
                fig2.update_layout(
                    barmode="group", title="Books & Patents per Candidate",
                    xaxis_title="Candidate", yaxis_title="Count",
                    yaxis=dict(range=[0, max(ar_df["total_books"].max(),
                                             ar_df["total_patents"].max(), 1) + 1]),
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Full Analysis Table")
            st.dataframe(ar_df, use_container_width=True)
        else:
            st.warning("No analysis results found.")

    #  TAB 2: Education 
    with tab2:
        st.subheader("Educational Records (Normalized & Ranked)")
        if not edu_df.empty:
            st.dataframe(edu_df, use_container_width=True)
            if "marks_normalized_percent" in edu_df.columns and not edu_df["marks_normalized_percent"].isnull().all():
                fig = px.box(edu_df, x="level", y="marks_normalized_percent",
                             title="Academic Performance Distribution by Level",
                             labels={"level": "Education Level", "marks_normalized_percent": "Score (%)"})
                st.plotly_chart(fig, use_container_width=True)
            if "ranking" in edu_df.columns:
                rank_counts = edu_df["ranking"].value_counts().reset_index()
                rank_counts.columns = ["ranking", "count"]
                st.plotly_chart(px.bar(rank_counts, x="ranking", y="count",
                                      title="Institution Ranking Distribution"),
                               use_container_width=True)
        else:
            st.write("No education records found.")

        if not ar_df.empty and "detected_gaps" in ar_df.columns:
            st.subheader("Educational Gap Analysis")
            for _, row in ar_df.iterrows():
                name = row.get("candidate_name", row.get("file_name", "Candidate"))
                gaps = row.get("detected_gaps", "")
                if gaps:
                    st.warning(f"**{name}:** {gaps}")
                else:
                    st.success(f"**{name}:** No significant educational gaps detected.")

    # TAB 3: Research 
    with tab3:
        st.subheader("Journal Publications Analysis")
        if not j_df.empty:
            st.dataframe(j_df, use_container_width=True)
            if "quartile" in j_df.columns:
                q_counts = j_df["quartile"].value_counts().reset_index()
                q_counts.columns = ["quartile", "count"]
                st.plotly_chart(px.pie(q_counts, names="quartile", values="count",
                                       title="Journal Quartile Distribution"),
                               use_container_width=True)
        else:
            st.write("No journal publications found.")

        st.subheader("Conference Publications Analysis")
        if not c_df.empty:
            st.dataframe(c_df, use_container_width=True)
            if "a_star_status" in c_df.columns:
                astar_counts = c_df["a_star_status"].value_counts().reset_index()
                astar_counts.columns = ["is_a_star", "count"]
                astar_counts["label"] = astar_counts["is_a_star"].map({True: "A* Conference", False: "Other"})
                st.plotly_chart(px.pie(astar_counts, names="label", values="count",
                                       title="Conference Quality (A* vs Others)"),
                               use_container_width=True)
        else:
            st.write("No conference publications found.")

    # TAB 4: Topic Variability 
    with tab4:
        st.subheader("Research Topic Variability Analysis")
        st.write(
            "This module classifies each publication into research themes and measures "
            "how focused or broad the candidate's research is."
        )
        if not t_df.empty:
            st.subheader("Per-Publication Topic Classification")
            st.dataframe(t_df, use_container_width=True)

            theme_counts = t_df["primary_theme"].value_counts().reset_index()
            theme_counts.columns = ["theme", "count"]
            fig_theme = px.bar(theme_counts, x="theme", y="count",
                               title="Research Theme Distribution (All Candidates)",
                               labels={"theme": "Research Theme", "count": "# Publications"},
                               color="theme")
            fig_theme.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_theme, use_container_width=True)

            if "candidate" in t_df.columns:
                candidates = t_df["candidate"].unique().tolist()
                selected   = st.selectbox("Select candidate for detailed topic breakdown:",
                                          candidates, key="topic_cand")
                cand_df    = t_df[t_df["candidate"] == selected]
                theme_per_cand = cand_df["primary_theme"].value_counts().reset_index()
                theme_per_cand.columns = ["theme", "count"]
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(px.pie(theme_per_cand, names="theme", values="count",
                                           title=f"Topic Distribution — {selected}"),
                                   use_container_width=True)
                with col2:
                    st.plotly_chart(px.bar(theme_per_cand, x="theme", y="count",
                                           title=f"Topic Counts — {selected}", color="theme"),
                                   use_container_width=True)

            if "year" in t_df.columns:
                trend_df = t_df[t_df["year"].astype(str).str.isnumeric()].copy()
                if not trend_df.empty:
                    trend_df["year"] = trend_df["year"].astype(int)
                    trend_agg = trend_df.groupby(["year", "primary_theme"]).size().reset_index(name="count")
                    st.plotly_chart(px.line(trend_agg, x="year", y="count", color="primary_theme",
                                            title="Research Topic Trend Over Time"),
                                   use_container_width=True)

            if not ar_df.empty and "research_diversity_score" in ar_df.columns:
                st.subheader("Research Diversity Scores per Candidate")
                div_df = ar_df[["candidate_name", "research_diversity_score",
                               "research_variability_label", "dominant_research_topic",
                               "topic_interpretation"]].copy()
                st.dataframe(div_df, use_container_width=True)
                st.plotly_chart(px.bar(div_df, x="candidate_name", y="research_diversity_score",
                                       color="research_variability_label",
                                       title="Research Diversity Score per Candidate (0=Specialist, 1=Interdisciplinary)"),
                               use_container_width=True)
        else:
            st.write("No publication data available for topic analysis.")

    #TAB 5: Co-Author Analysis 
    with tab5:
        st.subheader("Co-Author Collaboration Analysis")
        st.write(
            "This module analyzes co-authorship patterns including recurring collaborators, "
            "team sizes, and collaboration diversity."
        )
        if not ca_df.empty:
            st.subheader("Per-Paper Co-Author Details")
            st.dataframe(ca_df, use_container_width=True)
            if "team_size" in ca_df.columns:
                st.plotly_chart(px.histogram(ca_df, x="team_size", nbins=10,
                                             title="Distribution of Team Sizes per Paper"),
                               use_container_width=True)
            if "candidate" in ca_df.columns and "team_size" in ca_df.columns:
                avg_team = ca_df.groupby("candidate")["team_size"].mean().reset_index()
                avg_team.columns = ["candidate", "avg_team_size"]
                st.plotly_chart(px.bar(avg_team, x="candidate", y="avg_team_size",
                                       title="Average Team Size per Candidate"),
                               use_container_width=True)

        if not ar_df.empty and "total_unique_coauthors" in ar_df.columns:
            st.subheader("Co-Author Summary per Candidate")
            coauth_summary = ar_df[["candidate_name", "total_unique_coauthors",
                                    "avg_authors_per_paper", "solo_papers",
                                    "frequent_collaborators", "coauthor_interpretation"]].copy()
            st.dataframe(coauth_summary, use_container_width=True)
            st.plotly_chart(px.bar(coauth_summary, x="candidate_name", y="total_unique_coauthors",
                                   title="Unique Co-Authors per Candidate", color="candidate_name"),
                           use_container_width=True)
            st.plotly_chart(px.bar(coauth_summary, x="candidate_name", y="avg_authors_per_paper",
                                   title="Average Co-Authors per Paper", color="candidate_name"),
                           use_container_width=True)
        else:
            st.write("No co-author data available.")

    #  TAB 6: Books & Patents 
    with tab6:
        st.subheader("Books Authored / Co-Authored")
        if not bk_df.empty:
            st.dataframe(bk_df, use_container_width=True)
            if "authorship_role" in bk_df.columns:
                role_counts = bk_df["authorship_role"].value_counts().reset_index()
                role_counts.columns = ["role", "count"]
                st.plotly_chart(px.pie(role_counts, names="role", values="count",
                                       title="Book Authorship Roles"), use_container_width=True)
            if "publisher_credibility" in bk_df.columns:
                cred_counts = bk_df["publisher_credibility"].value_counts().reset_index()
                cred_counts.columns = ["credibility", "count"]
                st.plotly_chart(px.pie(cred_counts, names="credibility", values="count",
                                       title="Publisher Credibility Distribution"), use_container_width=True)
            if "candidate" in bk_df.columns:
                bk_per_cand = bk_df.groupby("candidate").size().reset_index(name="book_count")
                st.plotly_chart(px.bar(bk_per_cand, x="candidate", y="book_count",
                                       title="Books per Candidate", color="candidate"),
                               use_container_width=True)
            if not ar_df.empty and "books_interpretation" in ar_df.columns:
                st.subheader("Books Interpretation")
                for _, row in ar_df.iterrows():
                    st.info(f"**{row.get('candidate_name','Candidate')}:** {row.get('books_interpretation','')}")
        else:
            st.write("No books found in the processed CVs.")

        st.markdown("---")
        st.subheader("Patents")
        if not pt_df.empty:
            st.dataframe(pt_df, use_container_width=True)
            if "inventor_role" in pt_df.columns:
                inv_counts = pt_df["inventor_role"].value_counts().reset_index()
                inv_counts.columns = ["role", "count"]
                st.plotly_chart(px.pie(inv_counts, names="role", values="count",
                                       title="Patent Inventor Roles"), use_container_width=True)
            if "country" in pt_df.columns:
                country_counts = pt_df[pt_df["country"] != "Not Stated"]["country"].value_counts().reset_index()
                if not country_counts.empty:
                    country_counts.columns = ["country", "count"]
                    st.plotly_chart(px.bar(country_counts, x="country", y="count",
                                           title="Patents by Country of Filing", color="country"),
                                   use_container_width=True)
            if "candidate" in pt_df.columns:
                pt_per_cand = pt_df.groupby("candidate").size().reset_index(name="patent_count")
                st.plotly_chart(px.bar(pt_per_cand, x="candidate", y="patent_count",
                                       title="Patents per Candidate", color="candidate"),
                               use_container_width=True)
            if "verification_url" in pt_df.columns:
                st.subheader("Patent Verification Links")
                st.dataframe(pt_df[["candidate", "patent_number", "title", "verification_url"]],
                            use_container_width=True)
            if not ar_df.empty and "patents_interpretation" in ar_df.columns:
                st.subheader("Patents Interpretation")
                for _, row in ar_df.iterrows():
                    st.info(f"**{row.get('candidate_name','Candidate')}:** {row.get('patents_interpretation','')}")
        else:
            st.write("No patents found in the processed CVs.")

    # TAB 7: Skills Analysis
    with tab7:
        st.subheader("Skills Analysis")
        st.write(
            "Breakdown of each candidate's technical and domain skills, "
            "categorized by type and ranked by frequency."
        )

        if not sk_df.empty:
            raw_skills_df = sk_df[~sk_df["skill"].str.startswith("[CATEGORY]")].copy()
            cat_df        = sk_df[sk_df["skill"].str.startswith("[CATEGORY]")].copy()
            cat_df["category"] = cat_df["skill"].str.replace("[CATEGORY] ", "", regex=False)

            st.subheader("Top Skills per Candidate")
            if not raw_skills_df.empty:
                st.dataframe(raw_skills_df, use_container_width=True)

                overall_top = raw_skills_df.groupby("skill")["frequency"].sum().reset_index()
                overall_top = overall_top.sort_values("frequency", ascending=False).head(20)
                st.plotly_chart(px.bar(overall_top, x="skill", y="frequency",
                                       title="Top 20 Skills Across All Candidates",
                                       labels={"skill": "Skill", "frequency": "Frequency"},
                                       color="skill"),
                               use_container_width=True)

                if "candidate" in raw_skills_df.columns:
                    candidates = raw_skills_df["candidate"].unique().tolist()
                    sel_cand   = st.selectbox("Select candidate for skills breakdown:",
                                              candidates, key="skills_cand")
                    cand_sk    = raw_skills_df[raw_skills_df["candidate"] == sel_cand].sort_values("frequency", ascending=False)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(px.bar(cand_sk, x="skill", y="frequency",
                                               title=f"Skills — {sel_cand}", color="skill"),
                                       use_container_width=True)
                    with col2:
                        st.plotly_chart(px.pie(cand_sk, names="skill", values="frequency",
                                               title=f"Skill Share — {sel_cand}"),
                                       use_container_width=True)

            if not cat_df.empty:
                st.subheader("Skill Category Distribution")
                cat_totals = cat_df.groupby("category")["frequency"].sum().reset_index()
                st.plotly_chart(px.pie(cat_totals, names="category", values="frequency",
                                       title="Skill Categories (All Candidates)"),
                               use_container_width=True)

                if "candidate" in cat_df.columns:
                    fig_cat = px.bar(cat_df, x="candidate", y="frequency", color="category",
                                     barmode="stack",
                                     title="Skill Category Distribution per Candidate",
                                     labels={"frequency": "Skill Count", "candidate": "Candidate"})
                    st.plotly_chart(fig_cat, use_container_width=True)

            if not ar_df.empty and "unique_skills" in ar_df.columns:
                st.subheader("Skills Summary per Candidate")
                sk_summary = ar_df[["candidate_name", "total_skills", "unique_skills",
                                    "top_skills", "skills_interpretation"]].copy()
                st.dataframe(sk_summary, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(px.bar(sk_summary, x="candidate_name", y="total_skills",
                                           title="Total Skill Mentions per Candidate",
                                           color="candidate_name"),
                                   use_container_width=True)
                with col2:
                    st.plotly_chart(px.bar(sk_summary, x="candidate_name", y="unique_skills",
                                           title="Unique Skills per Candidate",
                                           color="candidate_name"),
                                   use_container_width=True)

                for _, row in ar_df.iterrows():
                    st.info(f"**{row.get('candidate_name','Candidate')}:** {row.get('skills_interpretation','')}")
        else:
            st.write("No skills data available.")

    #  TAB 8: Experience Analysis 
    with tab8:
        st.subheader("Professional Experience Analysis")
        st.write(
            "Total years of experience, number of roles, average tenure, "
            "and career progression trajectory for each candidate."
        )

        if not ex_df.empty:
            st.subheader("Per-Role Experience Details")
            st.dataframe(ex_df, use_container_width=True)

            if "duration_years" in ex_df.columns:
                st.plotly_chart(px.histogram(ex_df, x="duration_years", nbins=10,
                                             title="Role Duration Distribution (Years)",
                                             labels={"duration_years": "Duration (Years)"}),
                               use_container_width=True)

            if "candidate" in ex_df.columns and "duration_years" in ex_df.columns:
                total_exp = ex_df.groupby("candidate")["duration_years"].sum().reset_index()
                total_exp.columns = ["candidate", "total_years"]
                st.plotly_chart(px.bar(total_exp, x="candidate", y="total_years",
                                       title="Total Experience Years per Candidate",
                                       color="candidate",
                                       labels={"total_years": "Total Years"}),
                               use_container_width=True)

            roles_count = ex_df.groupby("candidate").size().reset_index(name="num_roles")
            st.plotly_chart(px.bar(roles_count, x="candidate", y="num_roles",
                                   title="Number of Roles per Candidate",
                                   color="candidate"),
                           use_container_width=True)

            if "candidate" in ex_df.columns and "start_year" in ex_df.columns:
                timeline_df = ex_df.dropna(subset=["start_year", "end_year"]).copy()
                if not timeline_df.empty:
                    timeline_df["start_year"] = timeline_df["start_year"].astype(int)
                    timeline_df["end_year"]   = timeline_df["end_year"].astype(int)
                    candidates_exp = timeline_df["candidate"].unique().tolist()
                    sel_exp = st.selectbox("Select candidate for career timeline:",
                                           candidates_exp, key="exp_cand")
                    cand_exp_df = timeline_df[timeline_df["candidate"] == sel_exp]
                    if not cand_exp_df.empty:
                        fig_gantt = px.timeline(
                            cand_exp_df.assign(
                                start=pd.to_datetime(cand_exp_df["start_year"].astype(str)),
                                end=pd.to_datetime(cand_exp_df["end_year"].astype(str)),
                            ),
                            x_start="start", x_end="end",
                            y="job_title", color="organization",
                            title=f"Career Timeline — {sel_exp}",
                        )
                        fig_gantt.update_yaxes(autorange="reversed")
                        st.plotly_chart(fig_gantt, use_container_width=True)

        if not ar_df.empty and "experience_years" in ar_df.columns:
            st.subheader("Experience Summary per Candidate")
            exp_summary = ar_df[["candidate_name", "experience_years", "total_roles",
                                 "avg_tenure_years", "career_progression",
                                 "experience_interpretation"]].copy()
            st.dataframe(exp_summary, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(exp_summary, x="candidate_name", y="experience_years",
                                       title="Total Experience Years", color="candidate_name"),
                               use_container_width=True)
            with col2:
                st.plotly_chart(px.bar(exp_summary, x="candidate_name", y="avg_tenure_years",
                                       title="Average Tenure per Role (Years)",
                                       color="candidate_name"),
                               use_container_width=True)

            if "career_progression" in exp_summary.columns:
                prog_counts = exp_summary["career_progression"].value_counts().reset_index()
                prog_counts.columns = ["progression", "count"]
                st.plotly_chart(px.pie(prog_counts, names="progression", values="count",
                                       title="Career Progression Types"),
                               use_container_width=True)

            for _, row in ar_df.iterrows():
                st.info(f"**{row.get('candidate_name','Candidate')}:** {row.get('experience_interpretation','')}")
        else:
            st.write("No experience data available.")

    # TAB 9: Supervision 
    with tab9:
        st.subheader("Student Supervision Analysis")
        st.write(
            "Evaluates the candidate's MS/PhD supervision record, co-authored publications "
            "with supervised students, and identifies candidates who need to provide supervision data."
        )

        if not ar_df.empty and "total_supervised" in ar_df.columns:
            sup_summary = ar_df[[
                "candidate_name", "supervision_main_ms", "supervision_main_phd",
                "supervision_co_ms", "supervision_co_phd",
                "total_supervised", "total_student_pubs", "supervision_interpretation",
            ]].copy()
            st.subheader("Supervision Summary per Candidate")
            st.dataframe(sup_summary, use_container_width=True)

            fig_sup = go.Figure()
            fig_sup.add_trace(go.Bar(name="Main Supervisor (MS)",  x=ar_df["candidate_name"], y=ar_df["supervision_main_ms"]))
            fig_sup.add_trace(go.Bar(name="Main Supervisor (PhD)", x=ar_df["candidate_name"], y=ar_df["supervision_main_phd"]))
            fig_sup.add_trace(go.Bar(name="Co-Supervisor (MS)",    x=ar_df["candidate_name"], y=ar_df["supervision_co_ms"]))
            fig_sup.add_trace(go.Bar(name="Co-Supervisor (PhD)",   x=ar_df["candidate_name"], y=ar_df["supervision_co_phd"]))
            fig_sup.update_layout(
                barmode="stack", title="Supervision Breakdown per Candidate",
                xaxis_title="Candidate", yaxis_title="Students Supervised",
            )
            st.plotly_chart(fig_sup, use_container_width=True)

            if "total_student_pubs" in ar_df.columns:
                st.plotly_chart(px.bar(ar_df, x="candidate_name", y="total_student_pubs",
                                       title="Publications Co-Authored with Supervised Students",
                                       color="candidate_name"),
                               use_container_width=True)

            st.subheader("Supervision Interpretation")
            for _, row in ar_df.iterrows():
                interp = row.get("supervision_interpretation", "")
                if "No supervision data" in str(interp):
                    st.warning(f"**{row.get('candidate_name','Candidate')}:** {interp}")
                else:
                    st.info(f"**{row.get('candidate_name','Candidate')}:** {interp}")

        if not sup_df.empty:
            pub_rows = sup_df[sup_df["pub_title"] != "[SUMMARY]"]
            if not pub_rows.empty:
                st.subheader("Publications Co-Authored with Supervised Students")
                st.dataframe(pub_rows, use_container_width=True)

        st.subheader("Supervision Data Request Emails")
        if not ar_df.empty and "supervision_email" in ar_df.columns:
            missing_sup = ar_df[ar_df["supervision_email"].astype(str).str.len() > 0]
            if not missing_sup.empty:
                for _, row in missing_sup.iterrows():
                    with st.expander(f"Email for {row.get('candidate_name','Candidate')}"):
                        st.code(row.get("supervision_email", ""), language=None)
            else:
                st.success("All candidates have provided supervision data.")
        else:
            st.write("No supervision data available.")

    #  TAB 10: Skill Alignment 
    with tab10:
        st.subheader("Skill Alignment Analysis")
        st.write(
            "Evaluates whether each claimed skill is supported by the candidate's "
            "professional experience and/or research publications. "
            "Skills are classified as Strongly Evidenced, Partially Evidenced, "
            "Weakly Evidenced, or Unsupported."
        )

        if not sal_df.empty:
            st.subheader("Per-Skill Evidence Detail")
            st.dataframe(sal_df, use_container_width=True)

            ev_counts = sal_df["evidence_level"].value_counts().reset_index()
            ev_counts.columns = ["evidence_level", "count"]
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.pie(ev_counts, names="evidence_level", values="count",
                                       title="Overall Skill Evidence Distribution",
                                       color_discrete_map={
                                           "Strongly Evidenced":  "#2ecc71",
                                           "Partially Evidenced": "#f39c12",
                                           "Weakly Evidenced":    "#e67e22",
                                           "Unsupported":         "#e74c3c",
                                       }),
                               use_container_width=True)
            with col2:
                if "candidate" in sal_df.columns:
                    ev_by_cand = sal_df.groupby(["candidate", "evidence_level"]).size().reset_index(name="count")
                    st.plotly_chart(px.bar(ev_by_cand, x="candidate", y="count",
                                           color="evidence_level", barmode="stack",
                                           title="Skill Evidence by Candidate",
                                           color_discrete_map={
                                               "Strongly Evidenced":  "#2ecc71",
                                               "Partially Evidenced": "#f39c12",
                                               "Weakly Evidenced":    "#e67e22",
                                               "Unsupported":         "#e74c3c",
                                           }),
                                   use_container_width=True)

            if "candidate" in sal_df.columns:
                cands = sal_df["candidate"].unique().tolist()
                sel_sa = st.selectbox("Select candidate for skill alignment detail:",
                                      cands, key="sa_cand")
                cand_sa = sal_df[sal_df["candidate"] == sel_sa]
                st.dataframe(cand_sa[["skill", "in_experience", "in_publications", "evidence_level"]],
                            use_container_width=True)

        if not ar_df.empty and "skills_strongly_evidenced" in ar_df.columns:
            st.subheader("Skill Alignment Summary per Candidate")
            align_summary = ar_df[[
                "candidate_name",
                "skills_strongly_evidenced", "skills_partially_evidenced",
                "skills_weakly_evidenced", "skills_unsupported",
                "skill_alignment_interpretation",
            ]].copy()
            st.dataframe(align_summary, use_container_width=True)

            fig_align = go.Figure()
            fig_align.add_trace(go.Bar(name="Strongly Evidenced",  x=ar_df["candidate_name"], y=ar_df["skills_strongly_evidenced"],  marker_color="#2ecc71"))
            fig_align.add_trace(go.Bar(name="Partially Evidenced", x=ar_df["candidate_name"], y=ar_df["skills_partially_evidenced"], marker_color="#f39c12"))
            fig_align.add_trace(go.Bar(name="Weakly Evidenced",    x=ar_df["candidate_name"], y=ar_df["skills_weakly_evidenced"],    marker_color="#e67e22"))
            fig_align.add_trace(go.Bar(name="Unsupported",         x=ar_df["candidate_name"], y=ar_df["skills_unsupported"],         marker_color="#e74c3c"))
            fig_align.update_layout(
                barmode="stack", title="Skill Evidence Breakdown per Candidate",
                xaxis_title="Candidate", yaxis_title="Number of Skills",
            )
            st.plotly_chart(fig_align, use_container_width=True)

            for _, row in ar_df.iterrows():
                st.info(f"**{row.get('candidate_name','Candidate')}:** {row.get('skill_alignment_interpretation','')}")
        else:
            st.write("No skill alignment data available.")

    #  TAB 11: Timeline Consistency
    with tab11:
        st.subheader("Timeline Consistency Analysis")
        st.write(
            "Detects overlaps between education and employment, concurrent jobs, "
            "and unexplained professional gaps. Flags suspicious patterns for clarification."
        )

        if not tl_df.empty:
            st.subheader("Timeline Issues & Warnings")
            st.dataframe(tl_df, use_container_width=True)

            sev_counts = tl_df["severity"].value_counts().reset_index()
            sev_counts.columns = ["severity", "count"]
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.pie(sev_counts, names="severity", values="count",
                                       title="Timeline Finding Severity Distribution",
                                       color_discrete_map={
                                           "Issue":   "#e74c3c",
                                           "Warning": "#f39c12",
                                           "Info":    "#3498db",
                                       }),
                               use_container_width=True)
            with col2:
                if "candidate" in tl_df.columns:
                    sev_cand = tl_df.groupby(["candidate", "severity"]).size().reset_index(name="count")
                    st.plotly_chart(px.bar(sev_cand, x="candidate", y="count",
                                           color="severity", barmode="stack",
                                           title="Timeline Findings per Candidate",
                                           color_discrete_map={
                                               "Issue":   "#e74c3c",
                                               "Warning": "#f39c12",
                                               "Info":    "#3498db",
                                           }),
                                   use_container_width=True)

            issues_df = tl_df[tl_df["severity"] == "Issue"]
            if not issues_df.empty:
                st.subheader("Issues Requiring Clarification")
                for _, row in issues_df.iterrows():
                    st.error(f"**{row.get('candidate','')}:** {row.get('description','')}")

            warn_df = tl_df[tl_df["severity"] == "Warning"]
            if not warn_df.empty:
                st.subheader("Warnings")
                for _, row in warn_df.iterrows():
                    st.warning(f"**{row.get('candidate','')}:** {row.get('description','')}")

            info_df = tl_df[tl_df["severity"] == "Info"]
            if not info_df.empty:
                with st.expander("Informational Notes"):
                    for _, row in info_df.iterrows():
                        st.info(f"**{row.get('candidate','')}:** {row.get('description','')}")

        if not ar_df.empty and "timeline_assessment" in ar_df.columns:
            st.subheader("Overall Timeline Assessment per Candidate")
            tl_summary = ar_df[["candidate_name", "timeline_issues", "timeline_warnings", "timeline_assessment"]].copy()
            st.dataframe(tl_summary, use_container_width=True)

            for _, row in ar_df.iterrows():
                n_issues = int(row.get("timeline_issues", 0) or 0)
                n_warn   = int(row.get("timeline_warnings", 0) or 0)
                msg      = row.get("timeline_assessment", "")
                if n_issues > 0:
                    st.error(f"**{row.get('candidate_name','')}:** {msg}")
                elif n_warn > 0:
                    st.warning(f"**{row.get('candidate_name','')}:** {msg}")
                else:
                    st.success(f"**{row.get('candidate_name','')}:** {msg}")
        else:
            st.write("No timeline data available.")

    # TAB 12: Candidate Summaries 
    with tab12:
        st.subheader("Candidate Profile Summaries")
        st.write(
            "Concise per-candidate summary highlighting key strengths, concerns, "
            "suitability assessment, and overall profile interpretation."
        )

        if not sum_df.empty:
            for _, row in sum_df.iterrows():
                name        = row.get("candidate_name", "Candidate")
                suitability = row.get("suitability", "")
                score       = row.get("final_score", 0)
                strengths   = row.get("strengths_text", "")
                concerns    = row.get("concerns_text", "")

                if "Highly Recommended" in str(suitability):
                    header_color = "🟢"
                elif "Reservations" in str(suitability):
                    header_color = "🟡"
                elif "Significant Gaps" in str(suitability):
                    header_color = "🔴"
                else:
                    header_color = "⚪"

                with st.expander(f"{header_color} {name}  —  Score: {score}/100  |  {suitability}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("** Key Strengths**")
                        if strengths and strengths != "None identified":
                            for s in str(strengths).split(";"):
                                if s.strip():
                                    st.markdown(f"- {s.strip()}")
                        else:
                            st.markdown("- None identified")
                    with col2:
                        st.markdown("** Key Concerns**")
                        if concerns and concerns != "None identified":
                            for c in str(concerns).split(";"):
                                if c.strip():
                                    st.markdown(f"- {c.strip()}")
                        else:
                            st.markdown("- None identified")

            st.subheader("Suitability Overview")
            suit_counts = sum_df["suitability"].value_counts().reset_index()
            suit_counts.columns = ["suitability", "count"]
            st.plotly_chart(px.bar(suit_counts, x="suitability", y="count",
                                   title="Candidates by Suitability Category",
                                   color="suitability"),
                           use_container_width=True)

            st.plotly_chart(px.bar(sum_df, x="candidate_name", y="final_score",
                                   color="suitability",
                                   title="Final Scores with Suitability Labels",
                                   labels={"candidate_name": "Candidate", "final_score": "Score (0–100)"}),
                           use_container_width=True)

            summary_csv_path = os.path.join(output_dir, "m3_candidate_summaries.csv")
            if os.path.exists(summary_csv_path):
                with open(summary_csv_path, "rb") as f:
                    st.download_button(
                        "Download Candidate Summaries CSV",
                        f,
                        "m3_candidate_summaries.csv",
                        "text/csv",
                    )
        else:
            st.warning("No candidate summaries available.")

    #  TAB 13: Candidate Ranking
    with tab13:
        st.subheader("Candidate Ranking Leaderboard")
        st.write(
            "Candidates are scored across **8 dimensions** and ranked by their "
            "final weighted score (0–100)."
        )
        st.caption(
            "Weights: Education 20% · Research 25% · Topic Diversity 10% · "
            "Collaboration 10% · Books 5% · Patents 5% · Skills 15% · Experience 10%"
        )

        if not ar_df.empty:
            rank_df = ar_df.copy()
            rank_df["final_score"] = rank_df.apply(compute_final_score, axis=1)
            rank_df = rank_df.sort_values(by="final_score", ascending=False).reset_index(drop=True)
            rank_df.insert(0, "rank", range(1, len(rank_df) + 1))

            rank_df["edu_score"]   = rank_df.apply(
                lambda r: score_education(r["highest_qualification"],
                                          r["academic_progression"],
                                          r["detected_gaps"]), axis=1)
            rank_df["res_score"]   = rank_df.apply(
                lambda r: score_research(r["journal_count"],
                                         r["conference_count"],
                                         r["research_interpretation"]), axis=1)
            rank_df["topic_score"] = rank_df["research_diversity_score"].apply(score_topic_diversity)
            rank_df["coll_score"]  = rank_df.apply(
                lambda r: score_collaboration(r["total_unique_coauthors"],
                                              r["avg_authors_per_paper"]), axis=1)
            rank_df["book_score"]  = rank_df["total_books"].apply(score_books)
            rank_df["pat_score"]   = rank_df["total_patents"].apply(score_patents)
            rank_df["skill_score"] = rank_df.apply(
                lambda r: score_skills(r.get("total_skills", 0),
                                       r.get("unique_skills", 0)), axis=1)
            rank_df["exp_score"]   = rank_df.apply(
                lambda r: score_experience(r.get("experience_years", 0),
                                           r.get("total_roles", 0)), axis=1)

            leaderboard_cols = [
                "rank", "candidate_name", "final_score",
                "edu_score", "res_score", "topic_score", "coll_score",
                "book_score", "pat_score", "skill_score", "exp_score",
            ]
            st.dataframe(
                rank_df[[c for c in leaderboard_cols if c in rank_df.columns]],
                use_container_width=True,
            )

            fig_rank = px.bar(
                rank_df, x="candidate_name", y="final_score",
                color="final_score", color_continuous_scale="RdYlGn",
                title="Candidate Final Scores (Higher = Better)",
                labels={"candidate_name": "Candidate", "final_score": "Final Score (0–100)"},
                text="final_score",
            )
            fig_rank.update_traces(textposition="outside")
            fig_rank.update_layout(yaxis=dict(range=[0, 105]), coloraxis_showscale=False)
            st.plotly_chart(fig_rank, use_container_width=True)

            st.subheader("Score Breakdown per Candidate")
            score_dims = ["edu_score", "res_score", "topic_score", "coll_score",
                          "book_score", "pat_score", "skill_score", "exp_score"]
            dim_labels = ["Education", "Research", "Topic Diversity", "Collaboration",
                          "Books", "Patents", "Skills", "Experience"]

            radar_fig = go.Figure()
            for _, row in rank_df.iterrows():
                values = [row[d] for d in score_dims] + [row[score_dims[0]]]
                radar_fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=dim_labels + [dim_labels[0]],
                    fill="toself",
                    name=row["candidate_name"],
                ))
            radar_fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title="Score Breakdown Radar Chart",
                showlegend=True,
            )
            st.plotly_chart(radar_fig, use_container_width=True)

            st.subheader("Weighted Score Contribution per Candidate")
            weights = {
                "Education (20%)":        ("edu_score",   0.20),
                "Research (25%)":         ("res_score",   0.25),
                "Topic Diversity (10%)":  ("topic_score", 0.10),
                "Collaboration (10%)":    ("coll_score",  0.10),
                "Books (5%)":             ("book_score",  0.05),
                "Patents (5%)":           ("pat_score",   0.05),
                "Skills (15%)":           ("skill_score", 0.15),
                "Experience (10%)":       ("exp_score",   0.10),
            }
            stacked_fig = go.Figure()
            for label, (col, weight) in weights.items():
                stacked_fig.add_trace(go.Bar(
                    name=label,
                    x=rank_df["candidate_name"],
                    y=(rank_df[col] * weight).round(2),
                ))
            stacked_fig.update_layout(
                barmode="stack",
                title="Weighted Score Contribution (stacks sum to Final Score)",
                xaxis_title="Candidate",
                yaxis_title="Weighted Points",
                yaxis=dict(range=[0, 105]),
            )
            st.plotly_chart(stacked_fig, use_container_width=True)

            ranking_csv_path = os.path.join(output_dir, "m3_candidate_ranking.csv")
            if os.path.exists(ranking_csv_path):
                with open(ranking_csv_path, "rb") as f:
                    st.download_button(
                        "Download Ranking CSV",
                        f,
                        "m3_candidate_ranking.csv",
                        "text/csv",
                    )
        else:
            st.warning("No analysis results available to rank.")