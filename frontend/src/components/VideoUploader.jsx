import { useState } from "react";

function VideoUploader({
    onUpload,
    loading,
}) {
    const [file, setFile] =
        useState(null);

    const handleSubmit = async (
        event
    ) => {

        event.preventDefault();

        if (!file) {
            return;
        }

        await onUpload(file);
    };

    return (
        <div className="input-panel">

            <div className="panel-title">
                CCTV Video Analysis
            </div>

            <p className="panel-description">
                Upload a CCTV video for
                person detection, tracking,
                crowd analysis and risk
                assessment.
            </p>

            <form
                onSubmit={handleSubmit}
            >

                <label className="file-input">

                    <input
                        type="file"
                        accept="video/*"
                        onChange={(event) =>
                            setFile(
                                event.target
                                    .files?.[0] ||
                                null
                            )
                        }
                    />

                    <span>
                        {file
                            ? file.name
                            : "Choose CCTV video"}
                    </span>

                </label>

                <button
                    type="submit"
                    className="primary-button"
                    disabled={
                        !file || loading
                    }
                >
                    {loading
                        ? "Uploading..."
                        : "Upload & Analyze"}
                </button>

            </form>

        </div>
    );
}

export default VideoUploader;