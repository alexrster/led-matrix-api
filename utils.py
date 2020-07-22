class proportional2(object):
    """
    Wraps an existing font array, and on on indexing, trims any leading
    or trailing zero column definitions. This works especially well
    with scrolling messages, as interspace columns are squeezed to a
    single pixel.
    """
    def __init__(self, font):
        self.font = font

    def __getitem__(self, ascii_code):
        bitmap = self.font[ascii_code]
        # Return a slim version of the space character
        if ascii_code == 32:
            return [0] * 2
        # Return the same size for ':' character
        elif ascii_code == 58:
            bitmap = [0x00, 0x24, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            return self._trim(bitmap) + [0]
        else:
            return self._trim(bitmap) + [0]

    def _trim(self, arr):
        nonzero = [idx for idx, val in enumerate(arr) if val != 0]
        if not nonzero:
            return []
        first = nonzero[0]
        last = nonzero[-1] + 1
        return arr[first:last]