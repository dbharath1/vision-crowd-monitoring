function RiskIndicator({
    summary,
}) {

    const latest =
        summary?.latest;


    const risk =
        latest?.risk_level ||
        "UNKNOWN";

    const congestion =
        latest?.congestion_level ||
        "UNKNOWN";


    return (
        <div className="information-card">

            <div className="panel-heading">

                <div>

                    <h2>
                        Risk Assessment
                    </h2>

                    <p>
                        Application-layer
                        crowd risk indication
                    </p>

                </div>

            </div>


            <div className="level-section">

                <span>
                    Risk Level
                </span>

                <strong
                    className={`level-badge ${risk.toLowerCase()}`}
                >
                    {risk}
                </strong>

            </div>


            <div className="score-section">

                <span>
                    Risk Score
                </span>

                <strong>
                    {latest?.risk_score !=
                    null
                        ? Number(
                              latest.risk_score
                          ).toFixed(3)
                        : "—"}
                </strong>

            </div>


            <div className="level-section">

                <span>
                    Congestion
                </span>

                <strong
                    className={`level-badge ${congestion.toLowerCase()}`}
                >
                    {congestion}
                </strong>

            </div>


            <div className="score-section">

                <span>
                    Congestion Score
                </span>

                <strong>
                    {latest
                        ?.congestion_score !=
                    null
                        ? Number(
                              latest.congestion_score
                          ).toFixed(3)
                        : "—"}
                </strong>

            </div>


            <div className="notice">

                Risk is generated from
                computed congestion,
                density, movement and
                group-level indicators.
                It is not presented as a
                trained PETS2009 risk
                classifier.

            </div>

        </div>
    );
}

export default RiskIndicator;