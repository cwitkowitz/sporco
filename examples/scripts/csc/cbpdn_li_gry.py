#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of the SPORCO package. Details of the copyright
# and user license can be found in the 'LICENSE.txt' file distributed
# with the package.

"""
Single-channel CSC
==================

This example demonstrates solving a convolutional sparse coding problem with a greyscale signal

  $$\mathrm{argmin}_\mathbf{x} \; \frac{1}{2} \left\| \sum_m \mathbf{d}_m * \mathbf{x}_{m} - \mathbf{s} \right\|_2^2 + \lambda \sum_m \| \mathbf{x}_{m} \|_1 \;,$$

where $\mathbf{d}_{m}$ is the $m^{\text{th}}$ dictionary filter, $\mathbf{x}_{m}$ is the coefficient map corresponding to the $m^{\text{th}}$ dictionary filter, and $\mathbf{s}$ is the input image.
"""



from __future__ import print_function
from builtins import input
from builtins import range

import pyfftw   # See https://github.com/pyFFTW/pyFFTW/issues/40
import numpy as np

from sporco import util
from sporco import plot
import sporco.metric as sm
from sporco.admm import cbpdn


"""
Load example image.
"""

img = util.ExampleImages().image('kodim23.png', scaled=True, gray=True,
                                idxexp=np.s_[160:416,60:316])


"""
Highpass filter example image.
"""

npd = 16
fltlmbd = 10
sl, sh = util.tikhonov_filter(img, fltlmbd, npd)


"""
Load dictionary and display it.
"""

D = util.convdicts()['G:12x12x72']
plot.imview(util.tiledict(D), fgsz=(7, 7))


"""
Set :class:`.admm.cbpdn.ConvBPDN` solver options.
"""

mu    = 1e-2
lmbda = 5e-2
opt = cbpdn.ConvBPDNLatInh.Options({'Verbose': True, 'MaxMainIter': 200,
                                    'RelStopTol': 5e-3, 'AuxVarObj': False})


"""
Initialise and run CSC solver.
"""

Wg = np.append(np.eye(36), np.eye(36), axis=-1)
b = cbpdn.ConvBPDNLatInh(D, sh, Wg, 12, lmbda, mu, opt, dimK=0)
X = b.solve()
print("ConvBPDN solve time: %.2fs" % b.timer.elapsed('solve'))


"""
Reconstruct image from sparse representation.
"""

shr = b.reconstruct().squeeze()
imgr = sl + shr
print("Reconstruction PSNR: %.2fdB\n" % sm.psnr(img, imgr))


"""
Split the activation group
"""

Xg1 = X[:,:,:,:,:36]
Xg2 = X[:,:,:,:,36:]


"""
Display low pass component and sum of absolute values of coefficient maps of highpass component.
"""

fig = plot.figure(figsize=(10, 10))
plot.subplot(2, 2, 1)
plot.imview(sl, title='Lowpass component', fig=fig)
plot.subplot(2, 2, 2)
plot.imview(np.sum(abs(Xg1), axis=b.cri.axisM).squeeze(),
            cmap=plot.cm.Blues, title='Sparse representation (First Half)', fig=fig)
plot.subplot(2, 2, 3)
plot.imview(np.sum(abs(Xg2), axis=b.cri.axisM).squeeze(),
            cmap=plot.cm.Blues, title='Sparse representation (Second Half)', fig=fig)
plot.subplot(2, 2, 4)
plot.imview(np.sum(abs(abs(Xg1) - abs(Xg2)), axis=b.cri.axisM).squeeze(),
            cmap=plot.cm.Blues, title='Difference Magnitude', fig=fig)
fig.show()


"""
Display original and reconstructed images.
"""

fig = plot.figure(figsize=(14, 7))
plot.subplot(1, 2, 1)
plot.imview(img, title='Original', fig=fig)
plot.subplot(1, 2, 2)
plot.imview(imgr, title='Reconstructed', fig=fig)
fig.show()


"""
Get iterations statistics from solver object and plot functional value, ADMM primary and dual residuals, and automatically adjusted ADMM penalty parameter against the iteration number.
"""

its = b.getitstat()
fig = plot.figure(figsize=(20, 5))
plot.subplot(1, 3, 1)
plot.plot(its.ObjFun, xlbl='Iterations', ylbl='Functional', fig=fig)
plot.subplot(1, 3, 2)
plot.plot(np.vstack((its.PrimalRsdl, its.DualRsdl)).T,
          ptyp='semilogy', xlbl='Iterations', ylbl='Residual',
          lgnd=['Primal', 'Dual'], fig=fig)
plot.subplot(1, 3, 3)
plot.plot(its.Rho, xlbl='Iterations', ylbl='Penalty Parameter', fig=fig)
fig.show()


# Wait for enter on keyboard
input()
