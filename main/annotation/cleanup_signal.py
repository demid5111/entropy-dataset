class SingleEventsEliminator:
    @staticmethod
    def eliminate(signal):
        signal.keep_only_pairs()
        try:
            signal.check_only_pairs_are_left()
        except ValueError:
            raise ValueError('Labels contain unmatched elements. Check again')
