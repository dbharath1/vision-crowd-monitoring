function BehaviourPanel({
    summary,
}) {

    const latest =
        summary?.latest;


    return (
        <div className="information-card">

            <div className="panel-heading">

                <div>

                    <h2>
                        Crowd Behaviour
                    </h2>

                    <p>
                        Behaviour classification
                    </p>

                </div>

            </div>


            <div className="behaviour-result">

                <span>
                    Detected Behaviour
                </span>

                <strong>
                    {latest?.behaviour ||
                        "Not Evaluated"}
                </strong>

            </div>


            <div className="detail-row">

                <span>
                    Model Status
                </span>

                <strong>
                    {latest
                        ?.behaviour_status ||
                        "NOT_EVALUATED"}
                </strong>

            </div>


            {latest
                ?.behaviour_status ===
                "NOT_EVALUATED" && (

                <div className="notice">

                    Behaviour classification
                    requires a trained
                    labelled model.

                </div>

            )}

        </div>
    );
}

export default BehaviourPanel;