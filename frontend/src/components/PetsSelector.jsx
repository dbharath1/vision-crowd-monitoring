import { useEffect, useState } from "react";

import {
    getPetsViews,
    analyzePetsView,
} from "../services/api";


function PetsSelector({
    onSessionCreated,
}) {
    const [views, setViews] = useState([]);
    const [selectedView, setSelectedView] =
        useState("");

    const [loading, setLoading] =
        useState(false);

    const [error, setError] =
        useState("");

    const [loadingViews, setLoadingViews] =
        useState(true);


    // =========================================
    // LOAD PETS VIEWS
    // =========================================

    useEffect(() => {

        let cancelled = false;

        const loadViews = async () => {

            try {

                setLoadingViews(true);
                setError("");

                const data =
                    await getPetsViews();

                if (!cancelled) {

                    setViews(
                        Array.isArray(
                            data?.views
                        )
                            ? data.views
                            : []
                    );

                }

            } catch (err) {

                if (!cancelled) {

                    setError(
                        err?.response?.data
                            ?.detail ||
                        err?.message ||
                        "Unable to load PETS2009 views."
                    );

                }

            } finally {

                if (!cancelled) {
                    setLoadingViews(false);
                }

            }
        };

        loadViews();

        return () => {
            cancelled = true;
        };

    }, []);


    // =========================================
    // ANALYZE SELECTED VIEW
    // =========================================

    const handleAnalyze = async () => {

        if (!selectedView) {

            setError(
                "Please select a PETS2009 view."
            );

            return;
        }

        try {

            setLoading(true);
            setError("");

            const result =
                await analyzePetsView(
                    selectedView
                );

            if (
                result?.session_id == null
            ) {

                throw new Error(
                    "Backend did not return a session ID."
                );

            }

            if (
                typeof onSessionCreated ===
                "function"
            ) {

                onSessionCreated(result);

            }

        } catch (err) {

            setError(
                err?.response?.data
                    ?.detail ||
                err?.message ||
                "Unable to start PETS2009 analysis."
            );

        } finally {

            setLoading(false);

        }
    };


    return (
        <div className="input-panel">

            <div className="panel-title">
                PETS2009 Dataset
            </div>

            <p className="panel-description">
                Select an available PETS2009
                image sequence from the
                configured dataset.
            </p>


            {error && (
                <div className="inline-error">
                    {error}
                </div>
            )}


            {loadingViews ? (

                <div className="loading-message">
                    Loading PETS2009 views...
                </div>

            ) : (

                <select
                    value={selectedView}
                    onChange={(event) => {

                        setSelectedView(
                            event.target.value
                        );

                        setError("");

                    }}
                    disabled={loading}
                >

                    <option value="">
                        Select PETS2009 view
                    </option>

                    {views.map((view) => (

                        <option
                            key={view.path}
                            value={view.path}
                        >
                            {view.name}{" "}
                            —{" "}
                            {view.image_count}{" "}
                            images
                        </option>

                    ))}

                </select>

            )}


            {!loadingViews &&
                views.length === 0 &&
                !error && (

                    <div className="empty-state">
                        No PETS2009 image
                        sequences were found.
                    </div>

                )}


            <button
                type="button"
                className="primary-button"
                onClick={handleAnalyze}
                disabled={
                    !selectedView ||
                    loading ||
                    loadingViews
                }
            >

                {loading
                    ? "Starting Analysis..."
                    : "Analyze PETS View"}

            </button>

        </div>
    );
}


export default PetsSelector;