from main.signal.point import Point


class Peak:
    def __init__(self):
        self.points = []

    def new_point(self, idx, value):
        self.points.append(Point(idx, value))

    def max_points(self):
        if not self.points:
            return None
        with_duplicates = sorted(self.points, key=lambda x: x.value, reverse=True)

        res = []
        for i in with_duplicates:
            if i.value not in res:
                res.append(i.value)
        if len(res) == 1:
            res.append(res[0])
        return res