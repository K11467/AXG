import unittest
from range_download import validate_chunk, chunk_ranges, collect_chunks


class RangeDownloadTests(unittest.TestCase):
    def test_partitions_include_short_last_chunk(self):
        self.assertEqual(chunk_ranges(10, 4), [(0, 3), (4, 7), (8, 9)])

    def test_refuses_ignored_or_wrong_ranges(self):
        validate_chunk(206, 'bytes 4-7/10', b'abcd', 4, 7, 10)
        for status, header, body in ((200, None, b'abcd'),
                                     (206, 'bytes 0-3/10', b'abcd'),
                                     (206, 'bytes 4-7/10', b'a')):
            with self.assertRaises(ValueError):
                validate_chunk(status, header, body, 4, 7, 10)

    def test_one_failed_chunk_does_not_discard_other_completed_chunks(self):
        items = [(i, (i, i)) for i in range(5)]
        saved = []
        def fetch(item):
            if item[0] == 0:
                raise OSError('temporary DNS failure')
            return item[0]
        failed = collect_chunks(items, fetch, saved.append, workers=2)
        self.assertEqual(sorted(saved), [1, 2, 3, 4])
        self.assertEqual(failed, [items[0]])
        failed_again = collect_chunks(failed, lambda item: item[0], saved.append, workers=2)
        self.assertEqual(failed_again, [])
        self.assertEqual(sorted(saved), list(range(5)))


if __name__ == '__main__':
    unittest.main()
