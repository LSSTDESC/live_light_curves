# Keep this file in this location, as it needs to be copied to a dynamic location for lightcurver

def parse_header(header):
    from dateutil import parser
    from astropy.time import Time
    exptime = header['exptime']
    gain = header['gain']
    time = Time(parser.parse(header['obstart']))
    return {'exptime': exptime, 'gain': gain, 'mjd': time.mjd}
