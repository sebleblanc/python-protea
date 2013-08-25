"""Ashly Audio DSP and products Python RS-232 interface library.

This library aims at providing a convenient and simple layer between a python
script and the

Available devices:

    .-------------------------------------.
    | Class name  | Description           |
    |-------------|-----------------------|
    | Protea      | Generic Protea device |
    | P424C       | Protea 4.24C          |
    | Ne2424M     | Protea ne24.24M       |
    '-------------------------------------'

As first parameter for these class, one must pass the name to the serial
interface (that will in turn get opened using the pyserial library), or a 
serial interface object that supports `read`, `write`, `flushInput` and
`flushOutput` methods.
"""

# Copyright (c) 2013 Sébastien Leblanc
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Protea, ne24.24M and 4.24C are registered trademarks of Ashly Audio Inc.


__all__ = ["Protea", "Ne2424M", "P424C"]

from protea.exceptions import (SerialInterfaceError,
                               InvalidMessageType,
                               InvalidMessageContent)

from time import sleep as _sleep

class Protea(object):
    """Base class for devices in the Protea family.

    Subclasses must define the _header property as an array of bytes.
    """

    _baudrate = 38400
    _midi_channel = 1
    _header = None
    _start_byte = 0xf0  # These are standard MIDI
    _stop_byte = 0xf7   #   SysEx start-end bytes

    def write_message(self, message_type, message_content):
        """
        message_content: bytes() array
        message_type: single byte
        """
        assert self._header, "Cannot read or write to undefined Protea model!"

        base_message = bytearray()
        base_message.append(self._start_byte)
        base_message += self._header
        base_message.append(message_type)

        message = (base_message + message_content)
        message.append(self._stop_byte)

        self._serial.flushOutput()
        self._serial.flushInput()

        self._serial.write(message)

    def __init__(self, serial_interface):
        if isinstance(serial_interface, str) or serial_interface is None:
            try:
                import serial
            except ImportError:
                raise SerialInterfaceError(
                    "pyserial module was not found and "
                    "no serial interface was provided.")
            else:
                self._serial = serial.Serial(
                    serial_interface or 0,
                    baudrate=self._baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,)
        else:
            self._serial = serial_interface

        self._serial.setTimeout(0.5)


class P424C(Protea):
    """Device class for the Protea 4.24C System Processor unit"""
    _baudrate = 9600

    def _force_9600bps(self):
        """This method is required because the 4.24C usually communicates in 31.25kbps,
        but since this is a non-standard speed for RS-232, the machine will switch to
        9600 bps after having received a couple of bytes at that speed.
        """

        self._serial.flushInput()
        self._serial.write(bytes([0]*6))
        preamble = self._serial.read(10)

        status = preamble == bytes([0xf9]*10)

        return status

    def __init__(self, serial_interface, midi_channel):
        if not ( 1 <= midi_channel <= 16):
            raise ValueError("The midi_channel value must be between 1 and 16")

        super(P424C, self).__init__(serial_interface)

        self._midi_channel = midi_channel

        self._force_9600bps()
        self._header = bytearray([0x00, 0x01, 0x2a, 0x03, midi_channel-1])

    def preset_recall(self, preset_number, muted=False):
        """Recalls a preset on the Protea 4.24C device"""

        if not (1 <= preset_number <= 30):
            raise ValueError("Recalled preset must be between 1 and 31")

        self.write_message(21, bytes([preset_number-1, 1]))
        response = self._serial.read(10)

        if not muted:
            # This technique  is necessary because of limitations in the 4.24C,
            # in which during recall, it seems to assign values to its DSP in a
            # sequential fashion, sometimes leading to temporarily insane
            # values, such as high gains in both inputs and outputs, if the
            # previous preset had high gain in outputs and the next preset has
            # high gain in inputs.
            #
            # Furthermore, recalling the preset a second time allows us to
            # safely mute all outputs, then to recall without muting (i.e. as
            # they were saved in memory), since the input gains are already at a
            # sane level by respect to the outputs.

            _sleep(3.5)
            self.write_message(21, bytes([preset_number-1, 0]))
            response = self._serial.read(10)


class Ne2424M(Protea):
    """Device class for the Protea ne24.24M matrix processor"""
    _header = bytearray([0x00, 0x01, 0x2a, 0x06, 0x00])

    @staticmethod
    def is_valid_message(message):
        """Checks the validity of a message.

        Messages in the Protea RS-232 protocol start
        with 0xf0 and end with 0xf7.
        """
        return message[0] == 0xf0 and message[-1] == 0xf7

    def get_message_length(self, message_type):
        """Depending on message type, this function might
        return a dict instead of an int. If this is the case, then
        the message length is equivalent to:

            returned_length[ message[ message_type_off +1 ] ]

        That is, the byte that is following the message type in the actual
        message will tell us how long the message is supposed to be.
        """

        try:
            length = self.get_message_length.message_lengths[message_type]
        except KeyError:
            raise InvalidMessageType(
                "Not a valid message type: {#x}".format(message_type))
        else:
            return length

    get_message_length.message_lengths = {
        0x00:  10,  # Data request
        0x01: {0x00: 33, 0x01: 160, 0x02: 180},  # Special case: Data response
        0x02:   8,  # Meter request
        0x03:  59,  # Meter response
        0x04:   8,  # Preset names request
        0x05: 708,  # Preset names response
        0x06:  29,  # Preset save
        0x07:  10,  # Preset recall
        0x08: {0x01: 160, 0x02: 180},  # Special case: Data download
        0x09:  29,  # Preset / channel name
        0x0a:  10,  # Polarity
        0x0b:  11,  # Pre-amp
        0x0c:  11,  # Gain
        0x0d:  12,  # Delay
        0x0e:  17,  # EQ filter
        0x0f:  14,  # Gate
        0x10:  15,  # Auto-leveler
        0x11:  13,  # Dynamic ducker
        0x12:  13,  # Mixer
        0x13:  14,  # Shelving (HPF/LPF)
        0x14:  15,  # Limiting
        0x15:  10,  # Channel muting
        0x16:  10,  # EQ status
        0x17:   9,  # Mute all
                    # No 0x18
        0x19:  11,  # Mixer muting
        0x1a:  10,  # Gain increment/decrement
        0x42:   9,  # Local preset recall
    }

    def write_message(self, message_type, message_content):
        """
        message_content: bytes() array
        message_type: single byte
        """
        base_message = bytearray()
        base_message.append(self._start_byte)
        base_message += self._header
        base_message.append(message_type)

        message = (base_message + message_content)
        message.append(self._stop_byte)

        self._serial.flushOutput()
        self._serial.flushInput()

        self._serial.write(message)

    def get_data_request(self, input_channel=None, output_channel=None):
        """General "data request" Protea function.

        This is used to fetch configuration information for the current preset,
        or information relative to the inputs and outputs, one at a time.

        Input and output are 1-based channel numbers between 1 and 60.

        DATA REQUEST MESSAGE TEMPLATE:

          7: 00     Data request
          8: xx     Data request type (00=config, 01=input, 02=output)
          9: yy     Channel number (00-3b: channel 1-60. 00 for config)
        """

        if input_channel and output_channel:
            raise ValueError("Either an audio input, output, or no parameter "
                             "at all must be passed to this function")

        elif input_channel:
            assert 0 < input_channel <= 60
            request_type = 0x01
            channel_number = input_channel - 1
        elif output_channel:
            assert 0 < output_channel <= 60
            request_type = 0x02
            channel_number = output_channel - 1
        else:
            request_type = 0x00
            channel_number = 0x00

        message_type = 0x00

        self.write_message(message_type,
                           bytes([request_type, channel_number]))

        response_length = self.get_message_length(0x01)[request_type]

        raw_response = self._serial.read(response_length)
        if not self.is_valid_message(raw_response):
            raise InvalidMessageContent("The Protea device sent an "
                                        "unrecognized message! ", raw_response)

        response = {}

        response["message_type"] = raw_response[6]
        response["response_type"] = raw_response[7]
        response["preset_name"] = (raw_response[8:28]
                                   .decode("ascii").rstrip("\x00"))
        response["preset_number"] = raw_response[30] + 1

        return response

    def preset_recall(self, preset, muted=False):
        """Recalls a local preset on the ne24.24M device.

        `preset` is an integer between 1 and 31.
        """

        if not (1 <= preset <= 31):
            raise ValueError("Recalled preset must be between 1 and 31")

        self.write_message(0x07, bytes([preset-1, 0x01 if muted else 0x00]))

        self._serial.read(10)

    def mute_all_outputs(self, mute=True):
        """Mutes all outputs of the ne24.24M"""

        self.write_message(0x17, bytes([0x01 if mute else 0x00]))
        self._serial.read(9)
