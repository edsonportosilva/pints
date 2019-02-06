#!/bin/sh

changeName()
{
  grep -rl "$1" ./pints/* | xargs perl -i -pe"s/$1/$2/g"
}


changeName UnknownNoiseLogLikelihood GaussianLogLikelihood
changeName KnownNoiseLogLikelihood GaussianKnownSigmaLogLikelihood
changeName MultimodalNormalLogPDF MultimodalGaussianLogPDF
changeName NormalLogPDF GaussianLogPDF
changeName HighDimensionalNormalLogPDF HighDimensionalGaussianLogPDF
changeName MultivariateNormalLogPrior MultivariateGaussianLogPrior
changeName NormalLogPrior GaussianLogPrior
changeName Normal Gaussian