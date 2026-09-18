from .results import RoutingError


def assemble_route_geometry(arcs):
    """Join traversal-oriented arc geometries without repeating junctions."""
    if not arcs:
        return ()
    assembled = list(arcs[0].geometry)
    for arc in arcs[1:]:
        if not assembled or not arc.geometry or assembled[-1] != arc.geometry[0]:
            raise RoutingError("Route arc geometries are not continuous.")
        assembled.extend(arc.geometry[1:])
    return tuple(assembled)
