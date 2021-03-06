"""

python version of the mirror reflectivity code and refractive index calculations in shadow

TODO: vectorization

"""

import numpy
import scipy.constants as codata

tocm = codata.h * codata.c / codata.e * 1e2 # 12398.419739640718e-8

class PreRefl(object):

    def __init__(self):

        self.prerefl_dict = None

    def read_preprocessor_file(self,filename):

        fp = open(filename) # Open file on read mode
        lines = fp.read().split("\n") # Create a list containing all lines
        fp.close() # Close file

        index_pointer = 0
        mylist = lines[index_pointer].split("    ")
        QMIN = float(mylist[0])
        QMAX = float(mylist[1])
        QSTEP = float(mylist[2])
        DEPTH0 = float(mylist[3])


        index_pointer += 1
        NREFL = int(lines[index_pointer])

        ZF1 = numpy.zeros(NREFL)
        ZF2 = numpy.zeros(NREFL)
        for i in range(NREFL):
            index_pointer += 1
            ZF1[i] = float(lines[index_pointer])
        for i in range(NREFL):
            index_pointer += 1
            ZF2[i] = float(lines[index_pointer])

        self.prerefl_dict = {"QMIN":QMIN,"QMAX":QMAX,"QSTEP":QSTEP,"DEPTH0":DEPTH0,"NREFL":NREFL,"ZF1":ZF1,"ZF2":ZF2}

    def preprocessor_info(self,verbose=False):

        print("\n========================================")
        print("         preprocesor PreRefl info         ")
        for k in self.prerefl_dict.keys():
            try:
                print(k,self.prerefl_dict[k][0])
            except:
                print(k,self.prerefl_dict[k])

        print("QMIN: %f  EMIN: %f "%(self.prerefl_dict["QMIN"], self.prerefl_dict["QMIN"] * tocm / (2*numpy.pi)))
        print("QMAX: %f  EMAX: %f "%(self.prerefl_dict["QMAX"], self.prerefl_dict["QMAX"] * tocm / (2*numpy.pi)))
        print("========================================")

    def info(self):
        return self.preprocessor_info()

    def get_refraction_index(self,energy1,verbose=False):

        wnum = 2*numpy.pi * energy1 / tocm

        QSTEP = self.prerefl_dict["QSTEP"]
        QMIN = self.prerefl_dict["QMIN"]

        index1 = (wnum - QMIN) / QSTEP
        index1 = numpy.array(index1).astype(int)

        if index1.max() > self.prerefl_dict["NREFL"]:
            raise Exception("Error: Photon energy above tabulated upper limit.")

        if index1.min() < 0:
            raise Exception("Error: Photon energy below tabulated lower limit.")

        # WNUM0 = QSTEP * int(index1) + QMIN
        WNUM0 = QSTEP * index1 + QMIN
        DEL_X = wnum - WNUM0
        DEL_X = DEL_X / QSTEP

        # index1 = int(index1)

        ALFA = self.prerefl_dict["ZF1"][index1] + (self.prerefl_dict["ZF1"][index1+1]-self.prerefl_dict["ZF1"][index1]) * DEL_X
        GAMMA = self.prerefl_dict["ZF2"][index1] + (self.prerefl_dict["ZF2"][index1+1]-self.prerefl_dict["ZF2"][index1]) * DEL_X

        print(">>>", ALFA.shape, GAMMA.shape)
        refraction_index = (1.0 - ALFA / 2) + (GAMMA / 2)*1j

        if verbose:
            print("   prerefl_test: calculates refraction index for a given energy")
            print("                 using a file created by the prerefl preprocessor.")
            print("   \n")

            print("------------------------------------------------------------------------" )
            print("Inputs: " )
            print("   energy [eV]:                       ",wnum * tocm / (2*numpy.pi))
            print("   wavelength [A]:                    ",(1.0/wnum) * 2 * numpy.pi*1e8 )
            print("   wavenumber (2 pi/lambda) [cm^-1]:  ",wnum )
            # wnum = 2*numpy.pi * energy1 / tocm
            print("Outputs: " )
            print("   refraction index = (1-delta) + i*beta : " )
            print("   delta:                          ",1.0-refraction_index.real )#1.0-rr_ind )
            print("   beta:                           ",refraction_index.imag) #rr_attenuation / (2*wnum) )
            print("   real(n):                        ",refraction_index.real )
            print("   attenuation coef [cm^-1]:       ",2*refraction_index.imag*wnum )
            print("------------------------------------------------------------------------" )


        return refraction_index

    def get_attenuation_coefficient(self,energy1,verbose=False):
        refraction_index = self.get_refraction_index(energy1,verbose=verbose)
        wnum = 2 * numpy.pi * energy1 / tocm

        return 2*refraction_index.imag*wnum

    def reflectivity_fresnel(self,photon_energy_ev=10000.0,grazing_angle_mrad=3.0,
                             roughness_rms_A=0.0, method=2):
        """
        Calculates the reflectivity of an interface using Fresnel formulas.

        Code adapted from XOP and SHADOW

        :param grazing_angle_mrad: scalar with grazing angle in mrad
        :param roughness_rms_A: scalar with roughness rms in Angstroms
        :param photon_energy_ev: scalar or array with photon energies in eV
        :param method: 0=Born&Wolf, 1=Parratt, 2=shadow3
        :return: (rs,rp,runp) the s-polarized, p-pol and unpolarized reflectivities
        """


        rs, rp = self.reflectivity_amplitudes_fresnel(photon_energy_ev=photon_energy_ev,
                                                      grazing_angle_mrad=grazing_angle_mrad,
                                                      roughness_rms_A=roughness_rms_A,
                                                      method=method)
        # refraction_index = self.get_refraction_index(photon_energy_ev)
        #
        # theta1 = grazing_angle_mrad * 1e-3     # in rad
        # rough1 = roughness_rms_A
        #
        # # ; epsi = 1 - alpha - i gamma
        # # alpha = 2.0D0*k*f1
        # # gamma = 2.0D0*k*f2
        #
        # alpha = 2 * (1.0 - refraction_index.real)
        # gamma = 2 * refraction_index.imag
        #
        # rho = (numpy.sin(theta1))**2 - alpha
        # rho += numpy.sqrt((numpy.sin(theta1)**2 - alpha)**2 + gamma**2)
        # rho = numpy.sqrt(rho / 2)
        #
        # rs1 = 4 * (rho**2) * (numpy.sin(theta1) - rho)**2 + gamma**2
        # rs2 = 4 * (rho**2) * (numpy.sin(theta1) + rho)**2 + gamma**2
        # rs = rs1 / rs2
        #
        # ratio1 = 4 * rho**2 * (rho * numpy.sin(theta1) - numpy.cos(theta1)**2)**2 + gamma**2 * numpy.sin(theta1)**2
        # ratio2 = 4 * rho**2 * (rho * numpy.sin(theta1) + numpy.cos(theta1)**2)**2 + gamma**2 * numpy.sin(theta1)**2
        # ratio = ratio1 / ratio2
        #
        # rp = rs * ratio
        # runp = 0.5 * (rs + rp)
        #
        # wavelength_m = codata.h * codata.c / codata.e / photon_energy_ev
        #
        # debyewaller = numpy.exp( -(4.0 * numpy.pi * numpy.sin(theta1) * rough1 / (wavelength_m * 1e10))**2 )
        #
        # return rs*debyewaller, rp*debyewaller, runp*debyewaller
        return numpy.abs(rs)**2, numpy.abs(rp)**2, numpy.abs(0.5 * (rs + rp))**2,

    def reflectivity_amplitudes_fresnel(self, photon_energy_ev=10000.0, grazing_angle_mrad=3.0, roughness_rms_A=0.0,
                                        method=2 # 0=born & wold, 1=parratt, 2=shadow3
                                        ):

        refraction_index_1 = 1.0
        refraction_index_2 = self.get_refraction_index(photon_energy_ev)

        theta1g = grazing_angle_mrad * 1e-3     # in rad
        theta1 = numpy.pi / 2 - theta1g
        rough1 = roughness_rms_A

        sin_theta1 = numpy.sin(theta1)
        cos_theta1 = numpy.sqrt(1 - sin_theta1**2, dtype=numpy.complex)

        sin_theta2 = refraction_index_1 * sin_theta1 / refraction_index_2
        cos_theta2 = numpy.sqrt(1 - sin_theta2**2, dtype=numpy.complex)


        if method == 0: # born & wolf
            rs1 = refraction_index_2 * cos_theta1 - refraction_index_1 * cos_theta2
            rs2 = refraction_index_2 * cos_theta1 + refraction_index_1 * cos_theta2
            rs = rs1 / rs2

            rp1 = refraction_index_1 * cos_theta1 - refraction_index_2 * cos_theta2
            rp2 = refraction_index_1 * cos_theta1 + refraction_index_2 * cos_theta2
            rp = rp1 / rp2

        elif method == 1: # parratt
            phi = theta1g
            delta1 = 1.0 - numpy.real(refraction_index_1)
            beta1 = numpy.imag(refraction_index_1)
            delta2 = 1.0 - numpy.real(refraction_index_2)
            beta2 = numpy.imag(refraction_index_2)
            f1 = numpy.sqrt(phi ** 2 - 2 * delta1 - 2 * 1j * beta1, dtype=numpy.complex)
            f2 = numpy.sqrt(phi ** 2 - 2 * delta2 - 2 * 1j * beta2, dtype=numpy.complex)
            rs = (f1 - f2) / (f1 + f2)
            rp = rs

        elif method == 2:
            # ; epsi = 1 - alpha - i gamma
            # alpha = 2.0D0*k*f1
            # gamma = 2.0D0*k*f2

            alpha = 2 * (1.0 - refraction_index_2.real)
            gamma = 2 * refraction_index_2.imag

            rho = (numpy.sin(theta1g)) ** 2 - alpha
            rho += numpy.sqrt((numpy.sin(theta1g) ** 2 - alpha) ** 2 + gamma ** 2)
            rho = numpy.sqrt(rho / 2)

            rs1 = 4 * (rho ** 2) * (numpy.sin(theta1g) - rho) ** 2 + gamma ** 2
            rs2 = 4 * (rho ** 2) * (numpy.sin(theta1g) + rho) ** 2 + gamma ** 2
            rs = rs1 / rs2

            ratio1 = 4 * rho ** 2 * (rho * numpy.sin(theta1g) - numpy.cos(theta1g) ** 2) ** 2 + gamma ** 2 * numpy.sin(
                theta1g) ** 2
            ratio2 = 4 * rho ** 2 * (rho * numpy.sin(theta1g) + numpy.cos(theta1g) ** 2) ** 2 + gamma ** 2 * numpy.sin(
                theta1g) ** 2
            ratio = ratio1 / ratio2

            rp = rs * ratio

            rs = numpy.sqrt(rs, dtype=numpy.complex)
            rp = numpy.sqrt(rp, dtype = numpy.complex)



        wavelength_m = codata.h * codata.c / codata.e / photon_energy_ev

        debyewaller = numpy.exp( -(4.0 * numpy.pi * numpy.sin(theta1g) * rough1 / (wavelength_m * 1e10))**2 )

        # runp = 0.5 * (rs + rp)
        # return numpy.abs(rs)**2 * debyewaller, numpy.abs(rp)**2 * debyewaller, numpy.abs(runp)**2 * debyewaller

        return rs * numpy.sqrt(debyewaller), rp * numpy.sqrt(debyewaller)


    #
    # this is copied (ans sligtly ceaned) from shadow3 python preprocessors
    #
    @classmethod
    def prerefl(cls, interactive=True, SYMBOL="SiC", DENSITY=3.217, FILE="prerefl.dat", E_MIN=100.0, E_MAX=20000.0,
                E_STEP=100.0):
        """
         Preprocessor for mirrors - python+xraylib version

         -"""

        # retrieve physical constants needed
        import scipy
        import xraylib

        import scipy.constants as codata

        tocm = codata.h * codata.c / codata.e * 1e2

        if interactive:
            # input section
            print("prerefl: Preprocessor for mirrors - python+xraylib version")
            iMaterial = input("Enter material expression (symbol,formula): ")
            density = input("Density [ g/cm3 ] ?")
            density = float(density)

            estart = input("Enter starting photon energy: ")
            estart = float(estart)

            efinal = input("Enter end photon energy: ")
            efinal = float(efinal)

            estep = input("Enter step photon energy:")
            estep = float(estep)

            out_file = input("Output file : ")
        else:
            iMaterial = SYMBOL
            density = DENSITY
            estart = E_MIN
            efinal = E_MAX
            estep = E_STEP
            out_file = FILE

        twopi = numpy.pi * 2
        npoint = int((efinal - estart) / estep + 1)
        depth0 = density / 2.0
        qmin = estart / tocm * twopi
        qmax = efinal / tocm * twopi
        qstep = estep / tocm * twopi

        f = open(out_file, 'wt')
        f.write(("%20.11e " * 4 + "\n") % tuple([qmin, qmax, qstep, depth0]))
        f.write("%i \n" % int(npoint))
        for i in range(npoint):
            energy = (estart + estep * i) * 1e-3
            tmp = 2e0 * (1e0 - xraylib.Refractive_Index_Re(iMaterial, energy, density))
            f.write("%e \n" % tmp)
        for i in range(npoint):
            energy = (estart + estep * i) * 1e-3
            tmp2 = 2e0 * (xraylib.Refractive_Index_Im(iMaterial, energy, density))
            f.write("%e \n" % tmp2)
        print("File written to disk: %s" % out_file)
        f.close()

        # test (not needed)
        itest = 0
        if itest:
            cdtest = xraylib.CompoundParser(iMaterial)
            print("    ", iMaterial, " contains %i atoms and %i elements" % (cdtest['nAtomsAll'], cdtest['nElements']))
            for i in range(cdtest['nElements']):
                print("    Element %i: %lf %%" % (cdtest['Elements'][i], cdtest['massFractions'][i] * 100.0))
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(qmin, qmax, qstep, depth0)
            print(npoint)
            for i in range(npoint):
                energy = (estart + estep * i) * 1e-3
                qq = qmin + qstep * i
                print(energy, qq, \
                      2e0 * (1e0 - xraylib.Refractive_Index_Re(iMaterial, energy, density)), \
                      2e0 * (xraylib.Refractive_Index_Im(iMaterial, energy, density)))
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        return None


if __name__ == "__main__":

    from srxraylib.plot.gol import plot

    #
    # refractive index
    #


    prerefl_file = "Be5_30.dat"
    PreRefl.prerefl(interactive=False, SYMBOL="Be", DENSITY=1.848, FILE=prerefl_file,
                    E_MIN=5000.0, E_MAX=30000.0, E_STEP=100.0)



    a = PreRefl()


    a.read_preprocessor_file(prerefl_file)

    refraction_index = a.get_refraction_index(10000.0,verbose=True)

    a.preprocessor_info()

    #
    # mirror reflectivity
    #

    a = PreRefl()

    prerefl_file = "Rh5_50.dat"
    PreRefl.prerefl(interactive=False, SYMBOL="Be", DENSITY=1.848, FILE=prerefl_file,
                    E_MIN=5000.0, E_MAX=50000.0, E_STEP=100.0)

    a.read_preprocessor_file(prerefl_file)

    Energy = numpy.linspace(5000.0,40000.0,100)

    RS0 = numpy.zeros_like(Energy)
    RS5 = numpy.zeros_like(Energy)

    a.preprocessor_info()

    #
    # scalar inputs
    #
    process_phase = False
    method = 2

    for ii,ee in enumerate(Energy):
        if process_phase:
            ss, pp = a.reflectivity_amplitudes_fresnel(grazing_angle_mrad=3.0, photon_energy_ev=ee,
                                                       roughness_rms_A=0.0, method=method)
            RS0[ii] = numpy.abs(ss)**2
            ss, pp = a.reflectivity_amplitudes_fresnel(grazing_angle_mrad=3.0, photon_energy_ev=ee,
                                                       roughness_rms_A=5.0, method=method)
            RS5[ii] = numpy.abs(ss)**2
        else:
            rs, rp, rav = a.reflectivity_fresnel(grazing_angle_mrad=3.0,photon_energy_ev=ee,
                                                 roughness_rms_A=0.0, method=method)
            RS0[ii] = rs
            rs, rp, rav = a.reflectivity_fresnel(grazing_angle_mrad=3.0,photon_energy_ev=ee,
                                                 roughness_rms_A=5.0, method=method)
            RS5[ii] = rs

    plot(Energy,RS0,Energy,RS5,ylog=True,legend=["no roughness","5A RMS roughness"],title="scalar inputs")



    # array inputs

    Grazing_angle = numpy.ones_like(Energy) * 3.0

    if process_phase:
        rs0, rp0 = a.reflectivity_amplitudes_fresnel(grazing_angle_mrad=Grazing_angle, photon_energy_ev=Energy,
                                                     roughness_rms_A=0.0)
        rs1, rp1 = a.reflectivity_amplitudes_fresnel(grazing_angle_mrad=Grazing_angle, photon_energy_ev=Energy,
                                                     roughness_rms_A=5.0)

        plot(Energy, numpy.abs(rs0)**2, Energy, numpy.abs(rs1)**2, ylog=True, legend=["no roughness", "5A RMS roughness"], title="array inputs")

    else:
        rs0, rp0, rav0 = a.reflectivity_fresnel(grazing_angle_mrad=Grazing_angle, photon_energy_ev=Energy, roughness_rms_A=0.0)
        rs1, rp1, rav1 = a.reflectivity_fresnel(grazing_angle_mrad=Grazing_angle, photon_energy_ev=Energy, roughness_rms_A=5.0)

        plot(Energy, rs0, Energy, rs1, ylog=True, legend=["no roughness", "5A RMS roughness"],title="array inputs")

