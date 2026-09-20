import {
    useEffect,
    useState,
} from "react";

import Header from "../components/Header";
import SourceSelector from "../components/SourceSelector";
import VideoUploader from "../components/VideoUploader";
import PetsSelector from "../components/PetsSelector";
import AnalysisStatus from "../components/AnalysisStatus";
import CrowdStats from "../components/CrowdStats";
import DensityChart from "../components/DensityChart";
import MovementChart from "../components/MovementChart";
import BehaviourPanel from "../components/BehaviourPanel";
import RiskIndicator from "../components/RiskIndicator";
import AlertPanel from "../components/AlertPanel";

import {
    uploadVideo,
    startAnalysis,
    getAnalysisStatus,
    getAnalysisSummary,
    getFrames,
    getAlerts,
} from "../services/api";


function Dashboard({
    onSessionCreated,
}) {

    const [source, setSource] =
        useState("video");

    const [sessionId, setSessionId] =
        useState(null);

    const [status, setStatus] =
        useState(null);

    const [summary, setSummary] =
        useState(null);

    const [frames, setFrames] =
        useState([]);

    const [alerts, setAlerts] =
        useState([]);

    const [loading, setLoading] =
        useState(false);

    const [error, setError] =
        useState("");


    // =========================================
    // VIDEO UPLOAD
    // =========================================

    const handleUpload = async (file) => {

        setLoading(true);
        setError("");

        try {

            const result =
                await uploadVideo(file);

            const id =
                result.session_id;

            if (
                id === undefined ||
                id === null
            ) {
                throw new Error(
                    "Backend did not return a session ID."
                );
            }

            setSessionId(id);

            if (
                typeof onSessionCreated ===
                "function"
            ) {
                onSessionCreated(id);
            }

            await startAnalysis(id);

        } catch (err) {

            setError(
                err?.response?.data?.detail ||
                err?.message ||
                "Unable to start video analysis."
            );

        } finally {

            setLoading(false);

        }
    };


    // =========================================
    // PETS SESSION
    // =========================================

    const handlePetsSession = (result) => {

        const id =
            result?.session_id;

        if (
            id === undefined ||
            id === null
        ) {
            setError(
                "Backend did not return a session ID."
            );

            return;
        }

        setSessionId(id);

        setError("");

        if (
            typeof onSessionCreated ===
            "function"
        ) {
            onSessionCreated(id);
        }
    };


    // =========================================
    // LOAD ANALYSIS DATA
    // =========================================

    useEffect(() => {

        if (
            sessionId === null ||
            sessionId === undefined
        ) {
            return;
        }

        let cancelled = false;


        const loadData = async () => {

            try {

                const [
                    statusData,
                    summaryData,
                    frameData,
                    alertData,
                ] = await Promise.all([

                    getAnalysisStatus(
                        sessionId
                    ),

                    getAnalysisSummary(
                        sessionId
                    ),

                    getFrames(
                        sessionId,
                        0,
                        300
                    ),

                    getAlerts(
                        sessionId
                    ),

                ]);


                if (cancelled) {
                    return;
                }


                setStatus(
                    statusData
                );

                setSummary(
                    summaryData
                );

                setFrames(
                    Array.isArray(frameData)
                        ? frameData
                        : []
                );

                setAlerts(
                    Array.isArray(alertData)
                        ? alertData
                        : []
                );


            } catch (err) {

                if (cancelled) {
                    return;
                }

                setError(
                    err?.response?.data?.detail ||
                    err?.message ||
                    "Unable to retrieve analysis data."
                );

            }

        };


        loadData();


        const interval =
            setInterval(
                loadData,
                3000
            );


        return () => {

            cancelled = true;

            clearInterval(
                interval
            );

        };

    }, [sessionId]);


    // =========================================
    // CHANGE SOURCE
    // =========================================

    const handleSourceChange = (
        newSource
    ) => {

        setSource(newSource);

        setSessionId(null);

        setStatus(null);

        setSummary(null);

        setFrames([]);

        setAlerts([]);

        setError("");

    };


    // =========================================
    // UI
    // =========================================

    return (

        <div className="app">

            <Header
                status={
                    status?.status
                }
            />


            <main className="main-content">

                {/* HERO */}

                <section className="hero">

                    <div>

                        <span className="eyebrow">
                            INTELLIGENT CROWD
                            ANALYSIS
                        </span>

                        <h2>
                            Monitor.
                            Understand.
                            Assess.
                        </h2>

                        <p>
                            A computer-vision
                            pipeline for person
                            detection, tracking,
                            crowd behaviour,
                            congestion and risk
                            assessment.
                        </p>

                    </div>

                </section>


                {/* SOURCE SELECTION */}

                <section className="analysis-input">

                    <SourceSelector
                        source={source}
                        setSource={
                            handleSourceChange
                        }
                    />


                    <div className="source-panel">

                        {source === "video" ? (

                            <VideoUploader
                                onUpload={
                                    handleUpload
                                }
                                loading={
                                    loading
                                }
                            />

                        ) : (

                            <PetsSelector
                                onSessionCreated={
                                    handlePetsSession
                                }
                            />

                        )}

                    </div>

                </section>


                {/* ERROR */}

                {error && (

                    <div className="error-banner">

                        {error}

                    </div>

                )}


                {/* STATUS */}

                {status && (

                    <AnalysisStatus
                        status={status}
                    />

                )}


                {/* CROWD OVERVIEW */}

                <section>

                    <div className="section-heading">

                        <div>

                            <span className="eyebrow">
                                LIVE ANALYSIS
                            </span>

                            <h2>
                                Crowd Overview
                            </h2>

                        </div>

                    </div>


                    <CrowdStats
                        summary={summary}
                    />

                </section>


                {/* CHARTS */}

                <section className="chart-grid">

                    <DensityChart
                        frames={frames}
                    />

                    <MovementChart
                        frames={frames}
                    />

                </section>


                {/* BEHAVIOUR + RISK */}

                <section className="result-grid">

                    <BehaviourPanel
                        summary={summary}
                    />

                    <RiskIndicator
                        summary={summary}
                    />

                </section>


                {/* ALERTS */}

                <section>

                    <AlertPanel
                        alerts={alerts}
                    />

                </section>

            </main>

        </div>

    );
}


export default Dashboard;