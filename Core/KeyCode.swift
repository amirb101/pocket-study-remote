import CoreGraphics

/// Typed key codes for use with `KeystrokeExecutor`.
///
/// Values are the standard macOS virtual key codes (kVK_* constants from
/// Carbon's HIToolbox/Events.h). Using a typed enum rather than raw integers
/// makes shortcut definitions self-documenting and prevents accidental mixups.
enum KeyCode: CGKeyCode {

    // MARK: - Letters

    case a = 0
    case b = 11
    case c = 8
    case d = 2
    case e = 14
    case f = 3
    case g = 5
    case h = 4
    case i = 34
    case j = 38
    case k = 40
    case l = 37
    case m = 46
    case n = 45
    case o = 31
    case p = 35
    case q = 12
    case r = 15
    case s = 1
    case t = 17
    case u = 32
    case v = 9
    case w = 13
    case x = 7
    case y = 16
    case z = 6

    /// `kVK_ANSI_3` — used for full-screen screenshot (⌘⇧3).
    case ansi3 = 20

    /// `kVK_ANSI_4` — used for region screenshot (⌘⇧4).
    case ansi4 = 21

    // MARK: - Punctuation and Brackets

    case leftBracket  = 33   // [
    case rightBracket = 30   // ]
    case backslash    = 42   // \
    case semicolon    = 41
    case apostrophe   = 39
    case comma        = 43
    case period       = 47
    case forwardSlash = 44
    case grave        = 50   // `
    case minus        = 27
    case equal        = 24

    // MARK: - Navigation

    case leftArrow  = 123
    case rightArrow = 124
    case downArrow  = 125
    case upArrow    = 126
    case pageUp     = 116
    case pageDown   = 121
    case home       = 115
    case end        = 119

    // MARK: - Special Keys

    case delete        = 51
    case forwardDelete = 117
    case escape        = 53
    case `return`      = 36
    case space         = 49
    case tab           = 48

    // MARK: - Function Keys

    case f1  = 122
    case f2  = 120
    case f3  = 99
    case f4  = 118
    case f5  = 96
    case f6  = 97
    case f7  = 98
    case f8  = 100
    case f9  = 101
    case f10 = 109
    case f11 = 103
    case f12 = 111
    case f13 = 105   // ⌨️ used for media: mute
    case f14 = 107   // volume down
    case f15 = 113   // volume up
}
