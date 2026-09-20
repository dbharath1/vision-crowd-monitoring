function TrackTable({
    tracks,
}) {

    return (
        <div className="table-panel">

            <div className="panel-heading">

                <div>

                    <h2>
                        Person Tracks
                    </h2>

                    <p>
                        ByteTrack identities
                        and movement
                    </p>

                </div>

            </div>


            {!tracks?.length ? (

                <div className="empty-state">
                    No tracking records
                    available.
                </div>

            ) : (

                <div className="table-wrapper">

                    <table>

                        <thead>

                            <tr>
                                <th>
                                    Frame
                                </th>

                                <th>
                                    ID
                                </th>

                                <th>
                                    Confidence
                                </th>

                                <th>
                                    X
                                </th>

                                <th>
                                    Y
                                </th>

                                <th>
                                    Speed
                                </th>

                                <th>
                                    Direction
                                </th>
                            </tr>

                        </thead>

                        <tbody>

                            {tracks.map(
                                (track, index) => (

                                    <tr
                                        key={`${track.frame_id}-${track.track_id}-${index}`}
                                    >

                                        <td>
                                            {
                                                track.frame_id
                                            }
                                        </td>

                                        <td>
                                            <strong>
                                                {
                                                    track.track_id
                                                }
                                            </strong>
                                        </td>

                                        <td>
                                            {track.confidence !=
                                            null
                                                ? Number(
                                                      track.confidence
                                                  ).toFixed(
                                                      2
                                                  )
                                                : "—"}
                                        </td>

                                        <td>
                                            {track.center?.[0] !=
                                            null
                                                ? Number(
                                                      track.center[0]
                                                  ).toFixed(
                                                      1
                                                  )
                                                : "—"}
                                        </td>

                                        <td>
                                            {track.center?.[1] !=
                                            null
                                                ? Number(
                                                      track.center[1]
                                                  ).toFixed(
                                                      1
                                                  )
                                                : "—"}
                                        </td>

                                        <td>
                                            {track.speed !=
                                            null
                                                ? `${Number(
                                                      track.speed
                                                  ).toFixed(
                                                      2
                                                  )} px/s`
                                                : "N/A"}
                                        </td>

                                        <td>
                                            {
                                                track.direction ||
                                                "—"
                                            }
                                        </td>

                                    </tr>

                                )
                            )}

                        </tbody>

                    </table>

                </div>

            )}

        </div>
    );
}

export default TrackTable;