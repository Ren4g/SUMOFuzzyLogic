"""Chạy: python fuzzy_v2/test_fuzzy.py; thêm --plot để vẽ bề mặt V2."""
import math
import sys
import unittest
from pathlib import Path

if __package__:
    from .fuzzy_controller import (
        fuzzy_green_time, normalize_queues, _mamdani, ACTIVITY_QUEUE,
    )
else:
    from fuzzy_controller import (
        fuzzy_green_time, normalize_queues, _mamdani, ACTIVITY_QUEUE,
    )


class TestFuzzyV2(unittest.TestCase):
    def test_mamdani_core_kept(self):
        # Mốc độc lập của lõi 9 luật cũ, trước hiệu chỉnh V2.
        for own, other, expected in [
            (30,5,40.4166667), (5,30,29.5833333),
            (20,20,35.), (40,0,51.6666667), (0,40,18.3333333),
        ]:
            self.assertAlmostEqual(_mamdani(own, other), expected, places=5)

    def test_empty_and_small_queues(self):
        self.assertEqual(fuzzy_green_time(0,0),10.)
        self.assertEqual(fuzzy_green_time(0,40),10.)
        self.assertLess(fuzzy_green_time(1,1), fuzzy_green_time(5,5))
        self.assertLess(fuzzy_green_time(5,5),35.)

    def test_large_queues_keep_ratio(self):
        self.assertEqual(normalize_queues(80,40),(40.,20.))
        self.assertEqual(normalize_queues(40,80),(20.,40.))
        self.assertGreater(fuzzy_green_time(80,40),fuzzy_green_time(40,80))

    def test_invalid_values(self):
        for value in [-1, math.nan, math.inf, -math.inf]:
            for pos in range(4):
                args=[5,5,0,0]
                args[pos]=value
                with self.subTest(value=value,pos=pos):
                    with self.assertRaises(ValueError):
                        fuzzy_green_time(*args)

    def test_optional_waiting_priority(self):
        base=fuzzy_green_time(20,20)
        self.assertGreater(fuzzy_green_time(20,20,60,0),base)
        self.assertLess(fuzzy_green_time(20,20,0,60),base)
        self.assertAlmostEqual(fuzzy_green_time(20,20,60,60),base)
        self.assertEqual(fuzzy_green_time(0,20,60,0),10.)
        self.assertEqual(fuzzy_green_time(5,0,0,60),fuzzy_green_time(5,0))

    def test_finite_bounds_and_repeatability(self):
        for own in [0,.1,1,5,10,20,40,80,1e6,1e308]:
            for other in [0,.1,5,20,40,80,1e6,1e308]:
                for waits in [(0,0),(0,120),(120,0)]:
                    value=fuzzy_green_time(own,other,*waits)
                    self.assertTrue(math.isfinite(value))
                    self.assertTrue(10<=value<=60)
                    self.assertEqual(value,fuzzy_green_time(own,other,*waits))

    def test_old_keyword_signature(self):
        self.assertEqual(fuzzy_green_time(ns_queue=5,ew_queue=10),
                         fuzzy_green_time(5,10))


def plot_control_surface():
    import numpy as np
    import matplotlib.pyplot as plt
    grid=np.linspace(0,80,41)
    x,y=np.meshgrid(grid,grid)
    z=np.array([[fuzzy_green_time(a,b) for a in grid] for b in grid])
    fig=plt.figure(figsize=(9,6))
    ax=fig.add_subplot(111,projection='3d')
    ax.plot_surface(x,y,z,cmap='viridis',vmin=10,vmax=60)
    ax.set(xlabel='Own queue',ylabel='Other queue',zlabel='Green (s)',
           title='V2: Mamdani + demand adjustment (waits = 0)',zlim=(10,60))
    folder=Path(__file__).resolve().parent/'figures'
    folder.mkdir(exist_ok=True)
    fig.savefig(folder/'control_surface.png',dpi=180,bbox_inches='tight')
    np.savetxt(folder/'control_surface.csv',np.column_stack([x.ravel(),y.ravel(),z.ravel()]),
               delimiter=',',header='own_queue,other_queue,green_seconds',comments='')
    print('Saved:',folder)
    plt.close(fig)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestFuzzyV2))
    if not result.wasSuccessful():
        raise SystemExit(1)
    if '--plot' in sys.argv:
        plot_control_surface()
