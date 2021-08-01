import math
from enum import IntEnum


class AltitudeUnit(IntEnum):
    METERS = 1
    FEET = 2


class PressureUnit(IntEnum):
    MBAR = 1
    MMHG = 2


class TemperatureUnit(IntEnum):
    CELSIUS = 1
    FARENHEIT = 2


class Constants:
    """
    Constants needed for environmental calculations
    """

    ADIABATIC_RELATIONSHIP = 5.255
    """Adiabatic Relationship of M * g / (R * a), in typical environments this is 5.255.
    source: https://de.wikipedia.org/wiki/Barometrische_Höhenformel#Typische_Temperaturgradienten"""

    EULERS_NUMBER = 2.718281828
    """ Euler's Number, often referred to as 'e'"""

    MOLAR_MASS_H20 = 18.01534
    """Molar mass of Water in [g / mol]"""

    TEMPERATURE_LAPSE_RATE = 0.0065
    """The rate with which temperature gets colder with increasing altitude.
    As mean over all weather scenarios this value is 0.0065 [K / m]
    source: https://de.wikipedia.org/wiki/Barometrische_Höhenformel#Typische_Temperaturgradienten"""

    UNIVERSAL_GAS_CONSTANT = 8.31447215
    """The universal gas constant, often referred to as 'R' in [J / mol / K]"""


class Conversions:
    """
    Conversion methods for units.
    These are all static methods because they could be functions as well,
    but seemed nicer to be collected in a class
    """

    @staticmethod
    def celsius_to_farenheit(temperature: float) -> float:
        """
        convert °C into °F
        :param temperature: in degrees Celsius
        :return: temperature in degrees Farenheit
        """
        return (temperature * (9.0 / 5.0)) + 32.0

    @staticmethod
    def celsius_to_kelvin(temperature: float) -> float:
        """
        convert °C in °K
        :param temperature: in degrees Celsius
        :return: temperature in degrees Kelvin
        """
        return temperature + 273.15

    @staticmethod
    def farenheit_to_celsius(temperature: float) -> float:
        """
        Convert °F in °C
        :param temperature: in degrees Farenheit
        :return: temperature in degrees Celsius
        """
        return (temperature * (5.0 / 9.0)) - 32.0

    @staticmethod
    def feet_to_meters(altitude: float) -> float:
        """
        Convert altitude in ft to m
        :param altitude:in feet
        :return: altitude in meters
        """
        return altitude / 3.28084

    @staticmethod
    def mmhg_to_mbar(pressure: float) -> float:
        """
        Convert mmHg in mbar (hPa)
        :param pressure: in millimeters of mercury
        :return: pressure in millibars
        """
        return pressure * 1.33322

    @staticmethod
    def meters_to_feet(altitude: float) -> float:
        """
        Convert m to ft
        :param altitude: in meters
        :return: altitude in feet
        """
        return altitude * 3.28084


def altitude(pressure: float,
             reference_pressure: float,
             pressure_unit: PressureUnit,
             temperature: float,
             temperature_unit: TemperatureUnit,
             altitude_unit: AltitudeUnit) -> float:
    """
    Calculate the local altitude based on the pressure and temperature.
    :param pressure: measured pressure at the station.
    :param reference_pressure: Pressure on MSL
    :param pressure_unit: :py:class:PressureUnit
    :param temperature: the measured temperature at the given pressure
    :param temperature_unit: :py:class:TemperatureUnit
    :param altitude_unit: :py:class:AltitudeUnit
    :return: local_altitude in py:class:AltitudeUnit
    """
    if temperature_unit == TemperatureUnit.FARENHEIT:
        temperature = Conversions.farenheit_to_celsius(temperature)
    if pressure_unit == PressureUnit.MMHG:
        pressure = Conversions.mmhg_to_mbar(pressure)
    local_altitude = (pow(reference_pressure / pressure, (1 / Constants.ADIABATIC_RELATIONSHIP)) - 1) * \
                     (Conversions.celsius_to_kelvin(temperature) / Constants.TEMPERATURE_LAPSE_RATE)
    if altitude_unit == AltitudeUnit.FEET:
        return Conversions.meters_to_feet(local_altitude)
    return local_altitude


def absolute_humidity(temperature: float, temperature_unit: TemperatureUnit, relative_humidity: float):
    """
    Calculate the absolute humidity in [g / m³]
    taken from https://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/
    precision is about 0.1°C in range -30 to 35°C
    August-Roche-Magnus 	6.1094 exp(17.625 x T)/(T + 243.04)
    Buck (1981) 		6.1121 exp(17.502 x T)/(T + 240.97)
    reference https://www.eas.ualberta.ca/jdwilson/EAS372_13/Vomel_CIRES_satvpformulae.html
    :param temperature: measured temperature
    :param temperature_unit: :py:class:TemperatureUnit
    :param relative_humidity: in percent
    :return: absolute humidity in grams per cubic meter
    """
    if temperature_unit == TemperatureUnit.FARENHEIT:
        temperature = Conversions.farenheit_to_celsius(temperature)
    temp = pow(Constants.EULERS_NUMBER,
               ((17.502 * temperature)
                / Conversions.celsius_to_kelvin(temperature)
                * Constants.UNIVERSAL_GAS_CONSTANT)
               )
    return 6.1121 * temp * Constants.MOLAR_MASS_H20 / (Conversions.celsius_to_kelvin(temperature)
                                                       * Constants.UNIVERSAL_GAS_CONSTANT)


def equivalent_sea_level_pressure(altitude: float, altitude_unit: AltitudeUnit,
                                  temperature: float, temperature_unit: TemperatureUnit,
                                  pressure: float) -> float:
    if temperature_unit == TemperatureUnit.FARENHEIT:
        temperature = Conversions.farenheit_to_celsius(temperature)
    if altitude_unit == AltitudeUnit.FEET:
        altitude = Conversions.feet_to_meters(altitude)
    temperature_lapse = Constants.TEMPERATURE_LAPSE_RATE * altitude
    return pressure / ((1 - temperature_lapse / (Conversions.celsius_to_kelvin(temperature) + temperature_lapse)) **
                       Constants.ADIABATIC_RELATIONSHIP)


def dew_point(temperature: float, temperature_unit: TemperatureUnit, relative_humidity: float) -> float:
    if temperature_unit == TemperatureUnit.FARENHEIT:
        temperature = Conversions.farenheit_to_celsius(temperature)
    dew_point = 243.04 * (math.log(relative_humidity / 100.0) + ((17.625 * temperature) / (243.04 + temperature))) / (
        17.625 - math.log(relative_humidity / 100.0) - ((17.625 * temperature) / (243.04 + temperature)))
    if temperature_unit == TemperatureUnit.FARENHEIT:
        dew_point = Conversions.celsius_to_farenheit(dew_point)
    return dew_point
