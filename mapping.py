def screen_to_complex(px, py, rect, top_left, bottom_right):
    rx = (px - rect.left) / rect.width
    ry = (py - rect.top) / rect.height
    x = top_left[0] + rx * (bottom_right[0] - top_left[0])
    y = top_left[1] + ry * (bottom_right[1] - top_left[1])
    return (x, y)

def complex_to_screen(x, y, rect, top_left, bottom_right):
    rx = (x - top_left[0]) / (bottom_right[0] - top_left[0])
    ry = (y - top_left[1]) / (bottom_right[1] - top_left[1])
    px = int(rect.left + rx * rect.width)
    py = int(rect.top + ry * rect.height)
    return (px, py)