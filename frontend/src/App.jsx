import { useState } from "react";

import Dashboard from "./pages/Dashboard";
import Analysis from "./pages/Analysis";


function App() {

    const [page, setPage] =
        useState("dashboard");

    const [
        activeSessionId,
        setActiveSessionId,
    ] = useState(null);


    const handleSessionCreated = (
        sessionId
    ) => {

        setActiveSessionId(
            Number(sessionId)
        );

        setPage("dashboard");

    };


    return (
        <>

            <nav className="navigation">

                <div className="nav-brand">

                    <span className="brand-icon">
                        C
                    </span>

                    <span>
                        CrowdWatch
                    </span>

                </div>


                <div className="nav-links">

                    <button
                        type="button"
                        className={
                            page ===
                            "dashboard"
                                ? "nav-link active"
                                : "nav-link"
                        }
                        onClick={() =>
                            setPage(
                                "dashboard"
                            )
                        }
                    >
                        Dashboard
                    </button>


                    <button
                        type="button"
                        className={
                            page ===
                            "analysis"
                                ? "nav-link active"
                                : "nav-link"
                        }
                        onClick={() =>
                            setPage(
                                "analysis"
                            )
                        }
                        disabled={
                            activeSessionId ===
                            null
                        }
                    >
                        Detailed Analysis
                    </button>

                </div>

            </nav>


            {page === "dashboard" ? (

                <Dashboard
                    onSessionCreated={
                        handleSessionCreated
                    }
                />

            ) : (

                <Analysis
                    sessionId={
                        activeSessionId
                    }
                />

            )}

        </>
    );
}


export default App;