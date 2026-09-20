function GroupTable({
    groups,
}) {

    return (
        <div className="table-panel">

            <div className="panel-heading">

                <div>

                    <h2>
                        Crowd Groups
                    </h2>

                    <p>
                        DBSCAN-based spatial
                        crowd grouping
                    </p>

                </div>

            </div>


            {!groups?.length ? (

                <div className="empty-state">
                    No crowd groups detected.
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
                                    Group
                                </th>

                                <th>
                                    Members
                                </th>

                                <th>
                                    Centroid
                                </th>

                                <th>
                                    Avg. Speed
                                </th>

                                <th>
                                    Avg. Displacement
                                </th>

                            </tr>

                        </thead>

                        <tbody>

                            {groups.map(
                                (
                                    group,
                                    index
                                ) => (

                                    <tr
                                        key={`${group.frame_id}-${group.group_id}-${index}`}
                                    >

                                        <td>
                                            {
                                                group.frame_id
                                            }
                                        </td>

                                        <td>
                                            <strong>
                                                {
                                                    group.group_id
                                                }
                                            </strong>
                                        </td>

                                        <td>
                                            {
                                                group.member_count
                                            }
                                        </td>

                                        <td>

                                            {group.centroid
                                                ? `${Number(
                                                      group.centroid[0]
                                                  ).toFixed(
                                                      1
                                                  )}, ${Number(
                                                      group.centroid[1]
                                                  ).toFixed(
                                                      1
                                                  )}`
                                                : "—"}

                                        </td>

                                        <td>

                                            {group.average_speed !=
                                            null
                                                ? `${Number(
                                                      group.average_speed
                                                  ).toFixed(
                                                      2
                                                  )} px/s`
                                                : "N/A"}

                                        </td>

                                        <td>

                                            {group.average_displacement !=
                                            null
                                                ? Number(
                                                      group.average_displacement
                                                  ).toFixed(
                                                      2
                                                  )
                                                : "—"}

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

export default GroupTable;