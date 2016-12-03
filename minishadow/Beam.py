import numpy
import scipy.constants as codata

# IMPORTANT: Column 11 is wavenumber (cm^-1) as internally in Shadow

class Beam(object):

    def __init__(self, N=1000, array=None):
        """

        :param N:
        :param array:
        :return:
        """
        if array is not None:
            ncol, N = array.shape
            if ncol != 18:
                raise Exception ("Bar array: must be [18,npoints]")

        self.rays = numpy.zeros((18,N))

    @classmethod
    def initialize_from_array(cls, array):
        """

        :param array:
        :return:
        """
        return Beam(array=array)

    @classmethod
    def initialize_as_pencil(cls, N=1000):
        """

        :param array:
        :return:
        """
        beam = Beam(N)
        beam.set_column(5,1.0) # Vy
        beam.set_column(7,1.0) # Es
        beam.set_column(10,1.0) # flag
        beam.set_column(11,2*numpy.pi/1e-8) # wavenumber (1 A)
        beam.set_column(12,numpy.arange(N,dtype=float)) # index

        return beam


    def duplicate(self):
        return Beam.initialize_from_array(self.rays.copy())

    #
    # getters
    #

    def get_number_of_rays(self,nolost=0):

        try:
            w = self.get_column(10)
        except Exception:
            print("Error: Empty beam...")
            return 0

        if nolost == 0:
            return w.size
        if nolost == 1:
            return numpy.array(numpy.where(w >= 0)).size
        if nolost == 2:
            return numpy.array(numpy.where(w < 0)).size


        return self.rays.shape[1]

    def get_photon_energy_eV(self):
        A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
        return self.get_column(11) / A2EV

    def get_photon_wavelength(self):
        return 2*numpy.pi/self.get_column(11) * 1e-2

    def get_intensity(self,nolost=0):
        w = self.get_column(23,nolost=nolost)
        return w.sum()

    def get_column(self,column,nolost=0):
        """
            Possible choice for column are:
             1   X spatial coordinate [user's unit]
             2   Y spatial coordinate [user's unit]
             3   Z spatial coordinate [user's unit]
             4   Xp direction or divergence [rads]
             5   Yp direction or divergence [rads]
             6   Zp direction or divergence [rads]
             7   X component of the electromagnetic vector (s-polariz)
             8   Y component of the electromagnetic vector (s-polariz)
             9   Z component of the electromagnetic vector (s-polariz)
            10   Lost ray flag
            11   wavenumber (2 pi / lambda[cm])
            12   Ray index
            13   Optical path length
            14   Phase (s-polarization) in rad
            15   Phase (p-polarization) in rad
            16   X component of the electromagnetic vector (p-polariz)
            17   Y component of the electromagnetic vector (p-polariz)
            18   Z component of the electromagnetic vector (p-polariz)

            19   Wavelength [A]
            20   R= SQRT(X^2+Y^2+Z^2)
            21   angle from Y axis
            22   the magnituse of the Electromagnetic vector
            23   |E|^2 (total intensity)
            24   total intensity for s-polarization
            25   total intensity for p-polarization
            26   K = 2 pi / lambda [A^-1]
            27   K = 2 pi / lambda * col4 [A^-1]
            28   K = 2 pi / lambda * col5 [A^-1]
            29   K = 2 pi / lambda * col6 [A^-1]
            30   S0-stokes = |Ep|^2 + |Es|^2
            31   S1-stokes = |Ep|^2 - |Es|^2
            32   S2-stokes = 2 |Es| |Ep| cos(phase_s-phase_p)
            33   S3-stokes = 2 |Es| |Ep| sin(phase_s-phase_p)

        :param column:
        :return:
        """

        if column <= 18:
            out = self.rays[column-1,:]
        else:
            A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
            col = column - 1
            ray = self.rays.T

            if col==10: out =  ray[:,col]/A2EV
            if col==18: out =  2*numpy.pi*1.0e8/ray[:,10]
            if col==19: out =  numpy.sqrt(ray[:,0]*ray[:,0]+ray[:,1]*ray[:,1]+ray[:,2]*ray[:,2])
            if col==20: out =  numpy.arccos(ray[:,4])
            if col==21: out =  numpy.sqrt(numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8,15,16,17] ]),axis=0))
            if col==22: out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8,15,16,17] ]),axis=0)
            if col==23: out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
            if col==24: out =  numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
            if col==25: out =  ray[:,10]*1.0e8
            if col==26: out =  ray[:,3]*ray[:,10]*1.0e8
            if col==27: out =  ray[:,4]*ray[:,10]*1.0e8
            if col==28: out =  ray[:,5]*ray[:,10]*1.0e8
            if col==29:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                out =  E2p+E2s
            if col==30:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                out =  E2p-E2s
            if col==31:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                Cos = numpy.cos(ray[:,13]-ray[:,14])
                out =  2*numpy.sqrt(E2s*E2p)*Cos
            if col==32:
                E2s = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [6,7,8] ]),axis=0)
                E2p = numpy.sum(numpy.array([ ray[:,i]*ray[:,i] for i in [15,16,17] ]),axis=0)
                Sin = numpy.sin(ray[:,13]-ray[:,14])
                out =  2*numpy.sqrt(E2s*E2p)*Sin

        if nolost == 0:
            return out.copy()

        if nolost == 1:
            f  = numpy.where(self.rays[9,:] > 0.0)
            if len(f[0])==0:
                print ('Beam.get_column: no GOOD rays, returning empty array')
                return numpy.empty(0)
            return out[f].copy()

        if nolost == 2:
            f  = numpy.where(self.rays[9,:] < 0.0)
            if len(f[0])==0:
                print ('Beam.get_column: no BAD rays, returning empty array')
                return numpy.empty(0)
            return out[f].copy()


    def get_standard_deviation(self,col, nolost=1, ref=0):
        '''
        returns the standard deviation of one viariable in the beam
        :param col: variable (shadow column number)
        :param nolost: 0 = use all rays, 1=good only, 2= lost only
        :param ref: 0 = no weight, 1=weight with intensity (col23)
        :return:
        '''
        x = self.get_column(col,nolost=nolost)
        if ref == 0:
            return x.std()
        else:
            w = self.get_column(23,nolost=nolost)
            average = numpy.average(x, weights=w)
            variance = numpy.average( (x-average)**2, weights=w)
            return(numpy.sqrt(variance))


    #
    # setters
    #

    def set_column(self,column,value):
        """
        :param column:
        :param value:
        :return:
        """
        self.rays[column-1,:] = value

    #
    # info
    #
    def info(self):
        """

        :return:
        """
        txt = ""
        txt += "Number of rays: %d \n"%(self.get_number_of_rays())
        txt += "Number of good rays: %d \n"%(self.get_number_of_rays(nolost=1))
        txt += "Mean energy: %f eV\n"%(self.get_photon_energy_eV().mean() )
        txt += "Mean wavelength: %f A\n"%(1e10 * self.get_photon_wavelength().mean() )
        txt += "Intensity: %f \n"%( self.get_intensity(nolost=1) )
        return txt

    #
    # propagation / movements
    #

    def retrace(self,dist,resetY=False):
        """

        :param dist:
        :param resetY:
        :return:
        """
        a0 = self.rays
        try:
            tof = (-a0[1,:] + dist)/a0[4,:]
            self.rays[0,:] += tof * self.rays[3,:]
            self.rays[1,:] += tof * self.rays[4,:]
            self.rays[2,:] += tof * self.rays[5,:]

            if resetY:
                self.rays[1,:] = 0.0

        except AttributeError:
            print ('Beam.retrace: No rays')


    def translation(self,qdist1):
        """

        :param qdist1: translation vector
        :return:

        """

        if numpy.array(qdist1).size != 3:
            raise Exception("Input must be a vector [x,y,z]")

        self.rays[0,:] += qdist1[0]
        self.rays[1,:] += qdist1[1]
        self.rays[2,:] += qdist1[2]


    def rotate(self,theta1,axis=1,rad=0):
        """

        :param theta1: the rotation angle in degrees (default=0)
        :param axis: The axis number (Shadow's column) for the rotation
                    (i.e, 1:x (default), 2:y, 3:z)
        :param file:
        :param rad: set this flag when theta1 is in radiants
        :return:
        """

        if not rad:
            theta1 = theta1 * numpy.pi / 180

        a1 = self.rays.copy()

        if axis == 1:
            torot = [2,3]
        elif axis == 2:
            torot = [1,3]
        elif axis == 3:
            torot = [1,2]


        costh = numpy.cos(theta1)
        sinth = numpy.sin(theta1)

        tstart = numpy.array([1,4,7,16])

        for i in range(len(tstart)):

            newaxis = axis + tstart[i] - 1
            newaxisi = newaxis - 1
            newtorot = torot + tstart[i] - 1
            newtoroti = newtorot -1

            self.rays[newtoroti[0],:] =  a1[newtoroti[0],:] * costh + a1[newtoroti[1],:] * sinth
            self.rays[newtoroti[1],:] = -a1[newtoroti[0],:] * sinth + a1[newtoroti[1],:] * costh
            self.rays[newaxisi]       =  a1[newaxisi,:]

    #
    # histograms
    #
    # TODO: histo1, histo2

def test_initialize():
    a = Beam(N=100)
    print(a.info())
    a = Beam(array=numpy.zeros( (18,1000) ))
    print(a.info())
    a = Beam.initialize_from_array(numpy.zeros( (18,1000) ))
    print(a.info())
    a = Beam.initialize_as_pencil(200)
    print(a.info())

if __name__ == "__main__":
    test_initialize()