import unittest
from dataclasses import replace
import numpy as np
from scipy.linalg import expm
from sdof import System, response, metrics, sweep, local_sensitivity, time_history


class FreeVibrationTests(unittest.TestCase):
    def test_response_against_independent_matrix_exponential(self):
        for z in (0,0.05,0.5,0.9999999,1,1.0000001,2,20):
            s=System(damping=z*20000)
            A=np.array([[0.,1.],[-s.stiffness/s.mass,-s.damping/s.mass]])
            for t in (0,0.001,0.15,1,10):
                expected=expm(A*t)@np.array([0.,s.v0])
                np.testing.assert_allclose(response(s,t),expected,rtol=1e-7,atol=1e-10)

    def test_peak_and_final_settling_all_regimes(self):
        for z in (0.001,0.05,0.5,0.99,1,1.01,2,20):
            s=System(damping=z*20000)
            r=metrics(s); peak=r['peak_displacement_m']; ts=r['settling_s']
            self.assertAlmostEqual(float(response(s,r['first_peak_s'])[1]),0,places=9)
            self.assertAlmostEqual(abs(float(response(s,ts)[0]))/peak,0.02,places=8)
            self.assertGreater(abs(float(response(s,ts-1e-7)[0])),0.02*peak)
            times=ts+np.linspace(1e-6,max(10,ts),20000)
            self.assertTrue(np.all(np.abs(response(s,times)[0])<=0.02000001*peak))

    def test_undamped_never_settles(self):
        self.assertTrue(np.isinf(metrics(System(damping=0))['settling_s']))

    def test_energy_dissipation(self):
        s=System(); t=np.linspace(0,10,10000); x,v=response(s,t)
        energy=0.5*s.mass*v*v+0.5*s.stiffness*x*x
        self.assertLess(np.max(np.diff(energy)),1e-10)

    def test_scaling_and_independence(self):
        base=System(); r=metrics(base)
        self.assertAlmostEqual(metrics(replace(base,mass=4000))['omega_n_rad_s'],5)
        self.assertAlmostEqual(metrics(replace(base,stiffness=400000))['omega_n_rad_s'],20)
        df=sweep(base,[0.5,1,2])
        self.assertEqual(len(df),9)
        self.assertTrue((df[df.parameter=='mass'].damping_N_s_m==base.damping).all())
        elastic=local_sensitivity()
        np.testing.assert_allclose(elastic.omega_n_rad_s,[-0.5,0.5,0],atol=1e-8)
        np.testing.assert_allclose(elastic.damping_ratio,[-0.5,-0.5,1],atol=1e-8)
        self.assertAlmostEqual(r['estimate_4_over_zeta_wn_s'],8)


    def test_general_initial_conditions_against_matrix_solution(self):
        for z in (0,.05,.99999999,1,1.00000001,2,20):
            for x0,v0 in ((.1,0),(-.1,.3),(.1,-3),(0,-.1),(0,0)):
                s=System(damping=z*20000,x0=x0,v0=v0)
                A=np.array([[0.,1.],[-s.stiffness/s.mass,-s.damping/s.mass]])
                for t in (0,.001,.15,1,10):
                    np.testing.assert_allclose(response(s,t),expm(A*t)@np.array([x0,v0]),atol=1e-9,rtol=1e-6)
                r=metrics(s)
                if np.isfinite(r['first_peak_s']):
                    self.assertAlmostEqual(float(response(s,r['first_peak_s'])[1]),0,places=8)
                ts=r['settling_s'];band=r['settling_band_m']
                if np.isfinite(ts) and ts>0:
                    self.assertAlmostEqual(abs(float(response(s,ts)[0])),band,places=9)
                    tail=ts+np.linspace(1e-8,max(ts,20),10000)
                    self.assertTrue(np.all(np.abs(response(s,tail)[0])<=band+1e-9))

    def test_rest_and_monotonic_cases(self):
        rest=metrics(System(x0=0,v0=0))
        self.assertEqual(rest['settling_s'],0)
        self.assertEqual(rest['peak_displacement_m'],0)
        self.assertTrue(np.isnan(rest['first_peak_s']))
        for c in (20000,40000):
            r=metrics(System(x0=.1,v0=0,damping=c))
            self.assertTrue(np.isnan(r['first_peak_s']))
            self.assertAlmostEqual(r['peak_displacement_m'],.1)
        self.assertTrue(np.isnan(local_sensitivity(System(damping=0)).loc['damping','omega_n_rad_s']))

    def test_ui_boundaries_and_physical_residual(self):
        from itertools import product
        for m,k,c,x,v in product((100.,100000.),(1000.,10000000.),(0.,100000.),(-.5,0.,.5),(-5.,0.,5.)):
            s=System(m,k,c,v,x);r=metrics(s,.001)
            self.assertTrue(np.isfinite(r['peak_displacement_m']))
            h=time_history(s,.1,100)
            residual=m*h.acceleration_m_s2+c*h.velocity_m_s+k*h.displacement_m
            np.testing.assert_allclose(residual,0,atol=1e-8)
            energy=h.total_energy_J.to_numpy()
            self.assertLessEqual(np.max(np.diff(energy)),max(1e-6,energy[0]*1e-10))

    def test_invalid_inputs(self):
        for kwargs in ({'mass':0},{'stiffness':-1},{'damping':-1},{'x0':np.nan},{'mass':np.nan}):
            with self.assertRaises(ValueError): System(**kwargs)
        for tol in (0,1,np.nan):
            with self.assertRaises(ValueError): metrics(System(),tol)

if __name__=='__main__': unittest.main()
