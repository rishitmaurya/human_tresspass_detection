# geometry.py
def is_inside_roi(center, roi):
    """
    Check if a point lies within a rectangular ROI.

    Args:
        center (tuple): (x, y) coordinates of point (e.g. person's center)
        roi (tuple): ((x1, y1), (x2, y2)) coordinates of the ROI

    Returns:
        bool: True if point is inside ROI
    """
    x, y = center
    (x1, y1), (x2, y2) = roi

    return x1 <= x <= x2 and y1 <= y <= y2
