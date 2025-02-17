import ee
ee.Initialize()

def aster_radiance(image):
  """
  Takes an ASTER image with pixel values in DN (as stored by Googel Earth Engine).
  Converts DN to at-sensor radiance across all bands.
  """
  image = image.select('B01', 'B02', 'B3N', 'B10', 'B11', 'B12', 'B13', 'B14')
  coefficients = ee.ImageCollection(
        image.bandNames().map(lambda band: ee.Image(image.getNumber(ee.String('GAIN_COEFFICIENT_').cat(band))).float())
    ).toBands().rename(image.bandNames())

  radiance = image.subtract(1).multiply(coefficients)

  return image.addBands(radiance, None, True)

def aster_reflectance(image):
  """
  Takes an ASTER image with pixel values in at-sensor radiance.
  Converts VIS/SWIR bands (B01 - B09) to at-sensor reflectance.
  """
  dayOfYear = image.date().getRelative('day', 'year')

  earthSunDistance = ee.Image().expression(
        '1 - 0.01672 * cos(0.01720209895 * (dayOfYear - 4))',
        {'dayOfYear': dayOfYear}
    )

  sunElevation = image.getNumber('SOLAR_ELEVATION')

  sunZen = ee.Image().expression(
        '(90 - sunElevation) * pi/180',
        {'sunElevation': sunElevation, 'pi': 3.14159265359}
    )

  reflectanceFactor = ee.Image().expression(
        'pi * pow(earthSunDistance, 2) / cos(sunZen)',
        {'earthSunDistance': earthSunDistance, 'sunZen': sunZen, 'pi': 3.14159265359}
    )

  #irradiance = [1845.99, 1555.74, 1119.47, 231.25, 79.81, 74.99, 68.66, 59.74, 56.92]
  irradiance = [1845.99, 1555.74, 1119.47]

  reflectance = image \
        .select('B01', 'B02', 'B3N').multiply(reflectanceFactor).divide(irradiance)

  return image.addBands(reflectance, None, True)

def aster_brightness_temp(image):
  """
  Takes an ASTER image with pixel values in at-sensor radiance.
  Converts TIR band B13 to at-satellite brightness temperature.
  """
  K1_vals = [866.468575]
  K2_vals = [1350.069147]
  T = image.expression('K2 / (log(K1/L + 1))',
                   {'K1': K1_vals, 'K2': K2_vals, 'L': image.select('B13')}
  )

  return image.addBands(T.rename('B13'), None, True)

def aster_brightness_temp_all_tir(image):
  """
  Takes an ASTER image with pixel values in at-sensor radiance.
  Converts TIR band B13 to at-satellite brightness temperature.
  """
  K1_vals = [3040.136402, 2482.375199, 1935.060183, 866.468575, 641.326517]
  K2_vals = [1735.337945, 1666.398761, 1585.420044, 1350.069147, 1271.221673]
  T = image.expression('K2 / (log(K1/L + 1))',
                   {'K1': K1_vals, 'K2': K2_vals, 'L': image.select('B10', 'B11', 'B12', 'B13', 'B14')}
  )

  return image.addBands(T.rename('B10', 'B11', 'B12', 'B13', 'B14'), None, True)

def aster_data_conversion(image):
  """
  Wrapper function that takes an aster image and converts all pixel values from 
  digital number to top-of-atmosphere reflectance (bands 1 - 9) and 
  at-satellite brightness temperature (bands 10 - 14).
  """
  img = aster_radiance(image)
  img = aster_reflectance(img)
  img = aster_brightness_temp_all_tir(img)
  return img
