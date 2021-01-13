#!/usr/bin/env python
# Copyright 2021, Tiger J. Wang
# Released under the MIT License, see project page for details
# https://github.com/tigerjwang/pyinputlanguage

import ctypes
import ctypes.util
import CoreFoundation
import Foundation
import objc

# In ObjC code, the workflow to switch input languages on a Mac looks like this:

# /* ----- Objective-C Code ----- */
# // https://stackoverflow.com/questions/23729704/change-osx-keyboard-layoutinput-source-programmatically-via-terminal-or-appl
# NSArray* sources = CFBridgingRelease(TISCreateInputSourceList((__bridge CFDictionaryRef)@{ (__bridge NSString*)kTISPropertyInputSourceID : @"com.apple.keylayout.French" }, FALSE));
# TISInputSourceRef source = (__bridge TISInputSourceRef)sources[0];
# OSStatus status = TISSelectInputSource(source);
# /* ----- End Objective-C ----- */

# This should be pretty easy to implement, but the only problem is that PyObjC doesn't wrap the "TISCreateInputSourceList" and "TISSelectInputSource" methods (in fact, in Python 3, the Carbon bridge is deprecated altogether in PyObjC).

# So we have to manually load the Carbon library and use ctypes to wrap those methods ourselves before we can call them.

# Example constants for inputSourceCode; for some reason there isn't a list somewhere mapping languages to their input method / keyboard layout codes, so let me know if you can't find one
KB_US = "com.apple.keylayout.US"
KB_FRENCH = "com.apple.keylayout.French"
IM_JAPANESE = "com.apple.inputmethod.Kotoeri.Japanese"

class InputLanguageNotFoundError(Exception):
    pass
class CarbonError(Exception):
    pass

"""
Switches input language on macOS system-wide to the input method / keyboard layout specified by the input source code.

:param inputSourceCode: system code for the target input method / keyboard layout; see examples above
:raises InputLanguageNotFoundError: if the input source specified by inputSourceCode cannot be found in the user's pallete of input languages 
:raises CarbonError: if the input source was found but the system is unable to switch input languages
"""
def macSwitchInputLanguage(inputSourceCode):
    # Mac machines will have the Carbon package, which contains Text Input Source Services methods
    carbon_path = ctypes.util.find_library('Carbon')
    carbon = ctypes.cdll.LoadLibrary(carbon_path)

    # Method to wrap a ObjC object pointer into a Python object
    # https://github.com/abarnert/pykeycode/blob/master/keycode.py
    _objc = ctypes.PyDLL(objc._objc.__file__)
    _objc.PyObjCObject_New.restype = ctypes.py_object
    _objc.PyObjCObject_New.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    def objcify(ptr):
        return _objc.PyObjCObject_New(ptr, 0, 1)

    # Wraps "TISCreateInputSourceList" method before calling
    carbon.TISCreateInputSourceList.argtypes = [ctypes.c_void_p, ctypes.c_bool]
    carbon.TISCreateInputSourceList.restype = ctypes.c_void_p
    # Wraps "TISSelectInputSource" method before calling
    carbon.TISSelectInputSource.argtypes = [ctypes.c_void_p]
    carbon.TISSelectInputSource.restype = ctypes.c_uint32 # OSStatus

    # Creates a properties dictionary that specifies the language input method we want to search for
    properties = Foundation.NSDictionary.dictionaryWithDictionary_({"TISPropertyInputSourceID": inputSourceCode})
    # To use our NSDictionary reference as an argument, we have to use its pointer
    properties_p = properties.__c_void_p__()    

    # Filters language input methods
    source_list_p = carbon.TISCreateInputSourceList(properties_p, False)
    source_list = objcify(source_list_p)
    if source_list == None:
        raise InputLanguageNotFoundError("The input method / keyboard layout specified was not found in the list of available input methodss / keyboard layouts of the user.")
    # We'll use the first TSMInputSource in the filtered list
    source = source_list[0]
    # To use our TSMInputSource reference as an argument, we have to use its pointer
    source_p = source.__c_void_p__()

    # Selects source
    status = carbon.TISSelectInputSource(source_p)
    if status != 0:
        raise CarbonError("Carbon API failed to switch input method / keyboard layout. Error code: {status}")
