import { useEffect, useState } from "react";

import TrackTable from "../components/TrackTable";
import GroupTable from "../components/GroupTable";

import {
    getTracks,
    getGroups,
} from "../services/api";


function Analysis({ sessionId }) {

    const [tracks, setTracks] = useState([]);

    const [groups, setGroups] = useState([]);

    const [frameId, setFrameId] = useState("");

    const [loading, setLoading] = useState(false);

    const [error, setError] = useState("");


    useEffect(() => {

        if (
            sessionId === null ||
            sessionId === undefined
        ) {
            return;
        }

        let cancelled = false;


        const loadAnalysisData = async () => {

            try {

                const selectedFrame =
                    frameId.trim() === ""
                        ? null
                        : Number(frameId);


                if (
                    selectedFrame !== null &&
                    (
                        !Number.isInteger(
                            selectedFrame
                        ) ||
                        selectedFrame < 1
                    )
                ) {

                    setError(
                        "Frame ID must be a positive integer."
                    );

                    return;
                }


                const [
                    trackData,
                    groupData,
                ] = await Promise.all([

                    getTracks(
                        sessionId,
                        selectedFrame
                    ),

                    getGroups(
                        sessionId,
                        selectedFrame
                    ),

                ]);


                if (cancelled) {
                    return;
                }


                setTracks(
                    Array.isArray(trackData)
                        ? trackData
                        : []
                );

                setGroups(
                    Array.isArray(groupData)
                        ? groupData
                        : []
                );

                setError("");


            } catch (err) {

                if (cancelled) {
                    return;
                }


                setTracks([]);

                setGroups([]);


                setError(
                    err?.response?.data?.detail ||
                    err?.message ||
                    "Unable to load analysis details."
                );


            } finally {

                if (!cancelled) {
                    setLoading(false);
                }

            }

        };


        loadAnalysisData();


        return () => {
            cancelled = true;
        };

    }, [sessionId, frameId]);


    if (
        sessionId === null ||
        sessionId === undefined
    ) {

        return (
            <div className="empty-page">

                <h2>
                    No active analysis
                </h2>

                <p>
                    Start an analysis from
                    the dashboard first.
                </p>

            </div>
        );

    }


    return (

        <div className="analysis-page">

            <div className="page-heading">

                <div>

                    <span className="eyebrow">
                        DETAILED ANALYSIS
                    </span>

                    <h2>
                        Detection &
                        Crowd Groups
                    </h2>

                </div>


                <div className="frame-filter">

                    <label htmlFor="frame-id">
                        Frame
                    </label>

                    <input
                        id="frame-id"
                        type="number"
                        min="1"
                        value={frameId}
                        placeholder="All"
                        onChange={(event) =>
                            setFrameId(
                                event.target.value
                            )
                        }
                    />

                </div>

            </div>


            {error && (

                <div className="error-banner">
                    {error}
                </div>

            )}


            {loading && (

                <div className="loading-message">
                    Loading analysis...
                </div>

            )}


            <TrackTable
                tracks={tracks}
            />


            <GroupTable
                groups={groups}
            />

        </div>

    );

}


export default Analysis;