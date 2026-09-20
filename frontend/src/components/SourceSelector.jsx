function SourceSelector({ source, setSource }) {
    return (
        <div className="source-selector">
            <div className="panel-title">
                Analysis Source
            </div>

            <p className="panel-description">
                Choose the source for crowd analysis.
            </p>

            <div className="source-options">
                <button
                    type="button"
                    className={
                        source === "video"
                            ? "source-option active"
                            : "source-option"
                    }
                    onClick={() => setSource("video")}
                >
                    <span className="source-option-title">
                        CCTV Video
                    </span>

                    <span className="source-option-description">
                        Analyze an uploaded CCTV/video file
                    </span>
                </button>

                <button
                    type="button"
                    className={
                        source === "pets"
                            ? "source-option active"
                            : "source-option"
                    }
                    onClick={() => setSource("pets")}
                >
                    <span className="source-option-title">
                        PETS2009 Clip
                    </span>

                    <span className="source-option-description">
                        Analyze PETS2009 ordered image frames
                    </span>
                </button>
            </div>
        </div>
    );
}

export default SourceSelector;