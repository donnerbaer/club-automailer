if (! lemonade && typeof(require) === 'function') {
    var lemonade = require('lemonadejs');
}

;(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    global.calendarjs = factory();
}(this, (function () {

var calendarjs;
/******/ (function() { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ 91:
/***/ (function(module) {

/**
 * (c) jSuites Javascript Plugins and Web Components (v6)
 *
 * Website: https://jsuites.net
 * Description: Create amazing web based applications.
 *
 * MIT License
 */

;(function (global, factory) {
     true ? module.exports = factory() :
    0;
}(this, (function () {

    'use strict';

    const Helpers = (function () {
        const component = {};

        // Excel like dates
        const excelInitialTime = Date.UTC(1900, 0, 0);
        const excelLeapYearBug = Date.UTC(1900, 1, 29);
        const millisecondsPerDay = 86400000;

        // Transform in two digits
        component.two = function (value) {
            value = '' + value;
            if (value.length === 1) {
                value = '0' + value;
            }
            return value;
        };

        component.isValidDate = function (d) {
            return d instanceof Date && !isNaN(d.getTime());
        };

        component.isValidDateFormat = function(date) {
            if (typeof date === 'string') {
                // Check format: YYYY-MM-DD using regex
                const match = date.substring(0, 10).match(/^(\d{4})-(\d{2})-(\d{2})$/);
                if (match) {
                    const year = Number(match[1]);
                    const month = Number(match[2]) - 1;
                    const day = Number(match[3]);
                    const parsed = new Date(Date.UTC(year, month, day));
                    // Return
                    return parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month && parsed.getUTCDate() === day;
                }
            }

            return false;
        }

        component.toString = function (date, dateOnly) {
            let y = null;
            let m = null;
            let d = null;
            let h = null;
            let i = null;
            let s = null;

            if (Array.isArray(date)) {
                y = date[0];
                m = date[1];
                d = date[2];
                h = date[3];
                i = date[4];
                s = date[5];
            } else {
                if (!date) {
                    date = new Date();
                }
                y = date.getUTCFullYear();
                m = date.getUTCMonth() + 1;
                d = date.getUTCDate();
                h = date.getUTCHours();
                i = date.getUTCMinutes();
                s = date.getUTCSeconds();
            }

            if (dateOnly === true) {
                return component.two(y) + '-' + component.two(m) + '-' + component.two(d);
            } else {
                return (
                    component.two(y) + '-' + component.two(m) + '-' + component.two(d) + ' ' + component.two(h) + ':' + component.two(i) + ':' + component.two(s)
                );
            }
        };

        component.toArray = function (value) {
            let date = value.split(value.indexOf('T') !== -1 ? 'T' : ' ');
            let time = date[1];

            date = date[0].split('-');
            let y = parseInt(date[0]);
            let m = parseInt(date[1]);
            let d = parseInt(date[2]);
            let h = 0;
            let i = 0;

            if (time) {
                time = time.split(':');
                h = parseInt(time[0]);
                i = parseInt(time[1]);
            }
            return [y, m, d, h, i, 0];
        };

        component.arrayToStringDate = function (arr) {
            return component.toString(arr, false);
        };

        component.dateToNum = function (jsDate) {
            if (typeof jsDate === 'string') {
                jsDate = new Date(jsDate + '  GMT+0');
            }
            let jsDateInMilliseconds = jsDate.getTime();
            if (jsDateInMilliseconds >= excelLeapYearBug) {
                jsDateInMilliseconds += millisecondsPerDay;
            }
            jsDateInMilliseconds -= excelInitialTime;

            return jsDateInMilliseconds / millisecondsPerDay;
        };

        component.numToDate = function (excelSerialNumber, asArray) {
            // allow 0; only bail on null/undefined/empty
            if (excelSerialNumber === null || excelSerialNumber === undefined || excelSerialNumber === '') {
                return '';
            }

            const MS_PER_DAY = 86_400_000;
            const SEC_PER_DAY = 86_400;

            // Excel day 0 is 1899-12-31 (with the fake 1900-02-29 at serial 60)
            const EXCEL_DAY0_UTC_MS = Date.UTC(1899, 11, 31);

            let wholeDays = Math.floor(excelSerialNumber);
            let fractionalDay = excelSerialNumber - wholeDays;

            // Fix the 1900 leap-year bug: shift serials >= 60 back one day
            if (wholeDays >= 60) wholeDays -= 1;

            // Build midnight UTC of the day
            let ms = EXCEL_DAY0_UTC_MS + wholeDays * MS_PER_DAY;

            // Add time part using integer seconds to avoid FP jitter
            const seconds = Math.round(fractionalDay * SEC_PER_DAY);
            ms += seconds * 1000;

            const d = new Date(ms);

            const arr = [
                d.getUTCFullYear(),
                component.two(d.getUTCMonth() + 1),
                component.two(d.getUTCDate()),
                component.two(d.getUTCHours()),
                component.two(d.getUTCMinutes()),
                component.two(d.getUTCSeconds()),
            ];

            return asArray ? arr : component.toString(arr, false);
        };

        component.prettify = function (d, texts) {
            if (!texts) {
                texts = {
                    justNow: 'Just now',
                    xMinutesAgo: '{0}m ago',
                    xHoursAgo: '{0}h ago',
                    xDaysAgo: '{0}d ago',
                    xWeeksAgo: '{0}w ago',
                    xMonthsAgo: '{0} mon ago',
                    xYearsAgo: '{0}y ago',
                };
            }

            if (d.indexOf('GMT') === -1 && d.indexOf('Z') === -1) {
                d += ' GMT';
            }

            let d1 = new Date();
            let d2 = new Date(d);
            let total = parseInt((d1 - d2) / 1000 / 60);

            const format = (t, o) => {
                return t.replace('{0}', o);
            };

            if (!total) {
                return texts.justNow;
            } else if (total < 90) {
                return format(texts.xMinutesAgo, total);
            } else if (total < 1440) {
                // One day
                return format(texts.xHoursAgo, Math.round(total / 60));
            } else if (total < 20160) {
                // 14 days
                return format(texts.xDaysAgo, Math.round(total / 1440));
            } else if (total < 43200) {
                // 30 days
                return format(texts.xWeeksAgo, Math.round(total / 10080));
            } else if (total < 1036800) {
                // 24 months
                return format(texts.xMonthsAgo, Math.round(total / 43200));
            } else {
                // 24 months+
                return format(texts.xYearsAgo, Math.round(total / 525600));
            }
        };

        component.prettifyAll = function () {
            let elements = document.querySelectorAll('.prettydate');
            for (let i = 0; i < elements.length; i++) {
                if (elements[i].getAttribute('data-date')) {
                    elements[i].innerHTML = component.prettify(elements[i].getAttribute('data-date'));
                } else {
                    if (elements[i].innerHTML) {
                        elements[i].setAttribute('title', elements[i].innerHTML);
                        elements[i].setAttribute('data-date', elements[i].innerHTML);
                        elements[i].innerHTML = component.prettify(elements[i].innerHTML);
                    }
                }
            }
        };

        // Compatibility with jSuites
        component.now = component.toString;

        const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

        const translate = function (t) {
            if (typeof document !== 'undefined' && document.dictionary) {
                return document.dictionary[t] || t;
            } else {
                return t;
            }
        };

        Object.defineProperty(component, 'weekdays', {
            get: function () {
                return weekdays.map(function (v) {
                    return translate(v);
                });
            },
        });

        Object.defineProperty(component, 'weekdaysShort', {
            get: function () {
                return weekdays.map(function (v) {
                    return translate(v).substring(0, 3);
                });
            },
        });

        Object.defineProperty(component, 'months', {
            get: function () {
                return months.map(function (v) {
                    return translate(v);
                });
            },
        });

        Object.defineProperty(component, 'monthsShort', {
            get: function () {
                return months.map(function (v) {
                    return translate(v).substring(0, 3);
                });
            },
        });

        return component;
    })();

    const Mask = (function() {
        // Currency
        const tokens = {
            // Escape
            escape: [ '\\\\[.\\s\\S]' ],
            // Text
            text: [ '@', '&' ],
            // Number
            fraction: [ '#{0,1}.*?\\?+\\/[0-9?]+' ],
            // Currency tokens
            currency: [ '#(.{1})##0?(.{1}0+)?( ?;(.*)?)?' ],
            // Scientific
            scientific: [ '[0#]+([.,]{1}0*#*)?E{1}\\+0+' ],
            // Percentage
            percentage: [ '[0#]+([.,]{1}0*#*)?%' ],
            // Number
            numeric: [ '[0#]+([.,]{1}0*#*)?', '#+' ],
            // Data tokens
            datetime: [ 'YYYY', 'YYY', 'YY', 'MMMMM', 'MMMM', 'MMM', 'MM', 'DDDDD', 'DDDD', 'DDD', 'DD', 'DY', 'DAY', 'WD', 'D', 'Q', 'MONTH', 'MON', 'HH24', 'HH12', 'HH', '\\[H\\]', 'H', 'AM/PM', 'MI', 'SS', 'MS', 'S', 'Y', 'M', 'I' ],
            // Other
            general: [ 'A', '0', '\\?', '\\*', ',,M', ',,,B', '[a-zA-Z\\$]+', '_[.\\s\\S]', '\\(', '\\)', '.']
        }

        const countryCodes = {
            "0409": [
                "$",
                ",",
                "."
            ],
            "0809": [
                "£",
                ",",
                "."
            ],
            "0C09": [
                "$",
                ",",
                "."
            ],
            "1009": [
                "$",
                ",",
                "."
            ],
            "1409": [
                "$",
                ",",
                "."
            ],
            "1809": [
                "€",
                ",",
                "."
            ],
            "1C09": [
                "R",
                " ",
                "."
            ],
            "040C": [
                "€",
                " ",
                ","
            ],
            "080C": [
                "€",
                " ",
                ","
            ],
            "100C": [
                "CHF",
                "'",
                "."
            ],
            "140C": [
                "€",
                " ",
                ","
            ],
            "0C0C": [
                "$",
                " ",
                ","
            ],
            "0407": [
                "€",
                ".",
                ","
            ],
            "0C07": [
                "€",
                ".",
                ","
            ],
            "0807": [
                "CHF",
                "'",
                "."
            ],
            "1007": [
                "€",
                ".",
                ","
            ],
            "0413": [
                "€",
                ".",
                ","
            ],
            "0813": [
                "€",
                " ",
                ","
            ],
            "0410": [
                "€",
                ".",
                ","
            ],
            "0810": [
                "CHF",
                "'",
                "."
            ],
            "0C0A": [
                "€",
                ".",
                ","
            ],
            "080A": [
                "$",
                ",",
                "."
            ],
            "2C0A": [
                "$",
                ".",
                ","
            ],
            "340A": [
                "$",
                ".",
                ","
            ],
            "240A": [
                "$",
                ".",
                ","
            ],
            "300A": [
                "$",
                ",",
                "."
            ],
            "280A": [
                "S/",
                ",",
                "."
            ],
            "200A": [
                "Bs.",
                ".",
                ","
            ],
            "140A": [
                "₡",
                ",",
                "."
            ],
            "100A": [
                "Q",
                ",",
                "."
            ],
            "1C0A": [
                "RD$",
                ",",
                "."
            ],
            "3C0A": [
                "$",
                ",",
                "."
            ],
            "440A": [
                "C$",
                ",",
                "."
            ],
            "4C0A": [
                "B/.",
                ",",
                "."
            ],
            "480A": [
                "L",
                ",",
                "."
            ],
            "0816": [
                "€",
                ".",
                ","
            ],
            "0416": [
                "R$",
                ".",
                ","
            ],
            "0406": [
                "kr",
                ".",
                ","
            ],
            "041D": [
                "kr",
                " ",
                ","
            ],
            "0414": [
                "kr",
                " ",
                ","
            ],
            "040B": [
                "€",
                " ",
                ","
            ],
            "040F": [
                "kr",
                ".",
                ","
            ],
            "0415": [
                "zł",
                " ",
                ","
            ],
            "0405": [
                "Kč",
                " ",
                ","
            ],
            "041B": [
                "€",
                " ",
                ","
            ],
            "040E": [
                "Ft",
                " ",
                ","
            ],
            "0424": [
                "€",
                ".",
                ","
            ],
            "041A": [
                "€",
                ".",
                ","
            ],
            "0418": [
                "lei",
                ".",
                ","
            ],
            "0402": [
                "лв.",
                " ",
                ","
            ],
            "0425": [
                "€",
                " ",
                ","
            ],
            "0426": [
                "€",
                " ",
                ","
            ],
            "0427": [
                "€",
                " ",
                ","
            ],
            "0408": [
                "€",
                ".",
                ","
            ],
            "043A": [
                "€",
                ",",
                "."
            ],
            "043C": [
                "€",
                ",",
                "."
            ],
            "0419": [
                "₽",
                " ",
                ","
            ],
            "0422": [
                "₴",
                " ",
                ","
            ],
            "0423": [
                "Br",
                " ",
                ","
            ],
            "041F": [
                "₺",
                ".",
                ","
            ],
            "042C": [
                "₼",
                " ",
                ","
            ],
            "042F": [
                "ден",
                ".",
                ","
            ],
            "0441": [
                "Lek",
                ".",
                ","
            ],
            "141A": [
                "KM",
                ".",
                ","
            ],
            "0401": [
                "ر.س",
                ",",
                "."
            ],
            "0C01": [
                "ج.م",
                ",",
                "."
            ],
            "1401": [
                "دج",
                " ",
                ","
            ],
            "1801": [
                "د.م.",
                " ",
                ","
            ],
            "1C01": [
                "د.ت",
                " ",
                ","
            ],
            "2001": [
                "﷼",
                ",",
                "."
            ],
            "3401": [
                "KD",
                ",",
                "."
            ],
            "3801": [
                "د.إ",
                ",",
                "."
            ],
            "3C01": [
                "BD",
                ",",
                "."
            ],
            "4001": [
                "ر.ق",
                ",",
                "."
            ],
            "2801": [
                "£",
                ",",
                "."
            ],
            "2C01": [
                "د.ا",
                ",",
                "."
            ],
            "3001": [
                "ل.ل",
                ",",
                "."
            ],
            "2401": [
                "﷼",
                ",",
                "."
            ],
            "1001": [
                "ل.د",
                ",",
                "."
            ],
            "0429": [
                "﷼",
                ",",
                "."
            ],
            "040D": [
                "₪",
                ",",
                "."
            ],
            "0439": [
                "₹",
                ",",
                "."
            ],
            "0445": [
                "৳",
                ",",
                "."
            ],
            "0461": [
                "रु",
                ",",
                "."
            ],
            "045B": [
                "Rs",
                ",",
                "."
            ],
            "044E": [
                "₹",
                ",",
                "."
            ],
            "0444": [
                "₹",
                ",",
                "."
            ],
            "0449": [
                "₹",
                ",",
                "."
            ],
            "044B": [
                "₹",
                ",",
                "."
            ],
            "0421": [
                "Rp",
                ".",
                ","
            ],
            "043E": [
                "RM",
                ",",
                "."
            ],
            "0464": [
                "₱",
                ",",
                "."
            ],
            "041E": [
                "฿",
                ",",
                "."
            ],
            "042A": [
                "₫",
                ".",
                ","
            ],
            "0453": [
                "៛",
                ",",
                "."
            ],
            "0454": [
                "₭",
                ",",
                "."
            ],
            "0455": [
                "K",
                ",",
                "."
            ],
            "0404": [
                "NT$",
                ",",
                "."
            ],
            "0C04": [
                "HK$",
                ",",
                "."
            ],
            "0804": [
                "¥",
                ",",
                "."
            ],
            "0411": [
                "¥",
                ",",
                "."
            ],
            "0412": [
                "₩",
                ",",
                "."
            ],
            "0437": [
                "₾",
                " ",
                ","
            ],
            "042B": [
                "֏",
                " ",
                ","
            ],
            "043F": [
                "₸",
                " ",
                ","
            ],
            "0443": [
                "so'm",
                " ",
                ","
            ],
            "0428": [
                "ЅМ",
                " ",
                ","
            ],
            "0440": [
                "сом",
                " ",
                ","
            ],
            "0466": [
                "₦",
                ",",
                "."
            ],
            "0469": [
                "₦",
                ",",
                "."
            ],
            "0468": [
                "GH₵",
                ",",
                "."
            ],
            "180C": [
                "F CFA",
                " ",
                ","
            ]
        }

        /**
         * Detect decimal and thousand separators in a mask pattern
         */
        const detectMaskSeparators = function(mask) {
            // Decimal: separator in pattern 0[sep]0+ (can have trailing chars like _ )
            // Look for the rightmost occurrence of this pattern
            const decimalMatches = mask.match(/0([.,\s'])0+/g);
            let decimal = null;
            if (decimalMatches && decimalMatches.length > 0) {
                // Get the last match (rightmost decimal pattern)
                const lastMatch = decimalMatches[decimalMatches.length - 1];
                const sepMatch = lastMatch.match(/0([.,\s'])0/);
                decimal = sepMatch ? sepMatch[1] : null;
            }

            // Thousand: other separator that appears in #[sep]# or 0[sep]# patterns
            let thousand = null;
            for (const sep of [',', '.', ' ', "'"]) {
                if (sep !== decimal) {
                    const escapedSep = sep === '.' ? '\\.' : sep;
                    const regex = new RegExp('[#0]' + escapedSep + '[#0]');
                    if (regex.test(mask)) {
                        thousand = sep;
                        break;
                    }
                }
            }

            return { decimal, thousand };
        }

        /**
         * Transform Excel currency locale patterns like [$$-409]#,##0.00
         * countryCodes format: { "0409": ["$", ",", "."] } // [currency, thousand, decimal]
         * [$$ = use locale's default currency, [$X = use literal X]
         */
        const transformExcelLocaleMask = function(mask) {
            // Handle multiple patterns (e.g., positive;negative)
            // Accept any alphanumeric for locale code to handle invalid codes gracefully
            const pattern = /\[\$(.?)-([0-9A-Z]+)\]/gi;
            let transformation = null;

            // Find first pattern to determine locale
            const firstMatch = mask.match(/\[\$(.?)-([0-9A-Z]+)\]/i);
            if (!firstMatch) return mask;

            const symbolChar = firstMatch[1] || '';
            let localeCode = firstMatch[2].toUpperCase();

            // Pad with leading zero if 3 digits (e.g., "409" → "0409")
            if (localeCode.length === 3) {
                localeCode = '0' + localeCode;
            }

            // Look up locale in countryCodes
            const localeData = countryCodes[localeCode];

            if (!localeData) {
                // Unknown locale - fallback: strip ALL patterns, use literal symbol (or $)
                const fallbackSymbol = symbolChar || '$';
                // Replace all occurrences of the pattern with the symbol
                return mask.replace(/\[\$(.?)-([0-9A-Z]+)\]/gi, fallbackSymbol);
            }

            // Extract from array: [currency, thousand, decimal]
            const localeCurrency = localeData[0];
            const localeThousand = localeData[1];
            const localeDecimal = localeData[2];

            // Determine currency symbol: $$ means use locale's default, else use literal
            let currencySymbol;
            if (symbolChar === '$') {
                // $$ pattern - use locale's default currency
                currencySymbol = localeCurrency;
            } else {
                // Literal symbol provided (e.g., [$€-407])
                currencySymbol = symbolChar;
            }

            // Replace all locale patterns with currency symbol
            let result = mask.replace(pattern, currencySymbol);

            // Detect current separators in mask (after removing patterns)
            const current = detectMaskSeparators(result);

            // Transform separators to match locale using placeholders to avoid conflicts
            const temp1 = '\uFFF0';  // Placeholder for thousand
            const temp2 = '\uFFF1';  // Placeholder for decimal

            // Step 1: Replace current separators with placeholders
            if (current.thousand && current.thousand !== localeThousand) {
                const from = current.thousand === '.' ? '\\.' : (current.thousand === ' ' ? ' ' : current.thousand);
                result = result.replace(new RegExp(from, 'g'), temp1);
            }
            if (current.decimal && current.decimal !== localeDecimal) {
                const from = current.decimal === '.' ? '\\.' : (current.decimal === ' ' ? ' ' : current.decimal);
                result = result.replace(new RegExp(from, 'g'), temp2);
            }

            // Step 2: Replace placeholders with target separators
            result = result.replace(new RegExp(temp1, 'g'), localeThousand);
            result = result.replace(new RegExp(temp2, 'g'), localeDecimal);

            return result;
        }

        // All expressions
        const allExpressions = [].concat(tokens.escape, tokens.fraction, tokens.currency, tokens.datetime, tokens.percentage, tokens.scientific, tokens.numeric, tokens.text, tokens.general).join('|');

        // Pre-compile all regexes once at initialization for better performance
        const compiledTokens = {};
        const tokenPriority = ['escape', 'fraction', 'currency', 'scientific', 'percentage', 'numeric', 'datetime', 'text', 'general'];

        // Cache for getMethod results
        const methodCache = {};
        // Cache for getTokens results
        const tokensCache = {};
        // Cache for autoCasting results
        const autoCastingCache = {};

        // Initialize compiled regexes
        for (const type of tokenPriority) {
            compiledTokens[type] = tokens[type].map(pattern => ({
                regex: new RegExp('^' + pattern + '$', 'i'),
                method: pattern
            }));
        }

        // Pre-compile regex for getTokens function
        const allExpressionsRegex = new RegExp(allExpressions, 'gi');
        const hiddenCaret = "\u200B";
        // Locale for date parsing
        const userLocale = (typeof navigator !== 'undefined' && navigator.language) || 'en-US';
        // Labels
        const weekDaysFull = Helpers.weekdays;
        const weekDays = Helpers.weekdaysShort;
        const monthsFull = Helpers.months;
        const months = Helpers.monthsShort;

        // Helpers

        const focus = function(el) {
            if (el.textContent.length) {
                // Handle contenteditable elements
                const range = document.createRange();
                const sel = window.getSelection();

                let node = el;
                // Go as deep as possible to the last text node
                while (node.lastChild) node = node.lastChild;
                // Ensure it's a text node
                if (node.nodeType === Node.TEXT_NODE) {
                    range.setStart(node, node.length);
                } else {
                    range.setStart(node, node.childNodes.length);
                }
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);

                el.scrollLeft = el.scrollWidth;
            }
        }

        /**
         * Returns if the given value is considered blank
         */
        const isBlank = function(v) {
            return v === null || v === '' || typeof(v) === 'undefined';
        }

        /**
         * Clean mask - extremely fast implementation using only char operations
         * Removes quotes, detects parenthesis for negative numbers, and removes brackets (except time format codes)
         * Sets control.parenthesisForNegativeNumbers and returns cleaned mask
         */
        const cleanMask = function(mask, control) {
            const len = mask.length;
            let result = '';

            for (let i = 0; i < len; i++) {
                const char = mask[i];

                // Remove quotes
                if (char === '"') {
                    continue;
                }

                // Handle brackets - remove them unless they're time format codes
                if (char === '[') {
                    // Check if it's a time format code: [s], [ss], [h], [hh], [m], [mm]
                    let isTimeFormat = false;
                    if (i + 2 < len && mask[i + 2] === ']') {
                        const c = mask[i + 1];
                        if (c === 's' || c === 'h' || c === 'm') {
                            isTimeFormat = true;
                        }
                    } else if (i + 3 < len && mask[i + 3] === ']') {
                        const c1 = mask[i + 1];
                        const c2 = mask[i + 2];
                        if ((c1 === 's' && c2 === 's') || (c1 === 'h' && c2 === 'h') || (c1 === 'm' && c2 === 'm')) {
                            isTimeFormat = true;
                        }
                    }

                    if (isTimeFormat) {
                        result += char;
                    } else {
                        // Skip content and closing bracket
                        while (i < len && mask[i] !== ']') {
                            i++;
                        }
                        continue;
                    }
                }
                // Check for parenthesis (not preceded by underscore and no underscore inside)
                else if (char === '(') {
                    if (i === 0 || mask[i - 1] !== '_') {
                        let hasUnderscore = false;
                        let depth = 1;
                        for (let j = i + 1; j < len && depth > 0; j++) {
                            if (mask[j] === '(') depth++;
                            if (mask[j] === ')') depth--;
                            if (mask[j] === '_') {
                                hasUnderscore = true;
                                break;
                            }
                        }
                        if (! hasUnderscore) {
                            control.parenthesisForNegativeNumbers = true;
                        }
                    }
                    result += char;
                } else {
                    result += char;
                }
            }

            return result;
        }

        /**
         * Receives a string from a method type and returns if it's a numeric method
         */
        const isNumeric = function(t) {
            return t === 'currency' || t === 'percentage' || t === 'numeric' || t === 'scientific';
        }

        const adjustPrecision = function(num) {
            if (typeof num === 'number' && ! Number.isInteger(num)) {
                const v = num.toString().split('.');

                if (v[1] && v[1].length > 10) {
                    let t0 = 0;
                    const t1 = v[1][v[1].length - 2];

                    if (t1 == 0 || t1 == 9) {
                        for (let i = v[1].length - 2; i > 0; i--) {
                            if (t0 >= 0 && v[1][i] == t1) {
                                t0++;
                                if (t0 > 6) {
                                    break;
                                }
                            } else {
                                t0 = 0;
                                break;
                            }
                        }

                        if (t0) {
                            return parseFloat(parseFloat(num).toFixed(v[1].length - 1));
                        }
                    }
                }
            }

            return num;
        }

        /**
         * Get the decimal defined in the mask configuration
         */
        const getDecimal = function(v) {
            let decimal;
            if (this.decimal) {
                decimal = this.decimal;
            } else {
                if (this.locale) {
                    let t = Intl.NumberFormat(this.locale).format(1.1);
                    decimal = t[1];
                } else {
                    if (! v) {
                        v = this.mask;
                    }

                    // Fixed regex: 0* means zero or more 0s before decimal separator
                    let e = new RegExp('0*([,.])0+', 'ig');
                    let t = e.exec(v);
                    if (t && t[1] && t[1].length === 1) {
                        decimal = t[1];
                    } else {
                        // Try the second pattern for # formats
                        e = new RegExp('#{1}(.{1})#+', 'ig');
                        t = e.exec(v);
                        if (t && t[1] && t[1].length === 1) {
                            if (t[1] === ',') {
                                decimal = '.';
                            } else if (t[1] === "'" || t[1] === '.') {
                                decimal = ',';
                            }
                        }
                    }

                    if (! decimal) {
                        decimal = '1.1'.toLocaleString().substring(1, 2);
                    }
                }
            }

            if (decimal) {
                return decimal;
            } else {
                return null;
            }
        }

        /**
         * Caret position getter
         * `this` in this function should be the element with a caret
         */
        const getCaretPosition = function(editableDiv) {
            let caretPos = 0;
            let sel = window.getSelection();
            if (sel && sel.rangeCount > 0) {
                let range = sel.getRangeAt(0);
                let preRange = range.cloneRange();
                preRange.selectNodeContents(editableDiv);
                preRange.setEnd(range.endContainer, range.endOffset);
                caretPos = preRange.toString().length;
            }
            return caretPos;
        }

        /**
         * Caret position getter
         * `this` in this function should be the element with a caret
         */
        const getCaret = function(el) {
            if (el.tagName === 'DIV') {
                return getCaretPosition(el);
            } else {
                return el.selectionStart;
            }
        }

        /**
         * Caret position setter
         * `this` should be the element (input/textarea or contenteditable div)
         */
        const setCaret = function(index) {
            if (typeof index !== 'number') index = Number(index) || 0;

            if (this.tagName !== 'DIV' || this.isContentEditable !== true) {
                const n = this.value ?? '';
                if (index < 0) index = 0;
                if (index > n.length) index = n.length;
                this.focus();
                this.selectionStart = index;
                this.selectionEnd = index;
                return;
            }

            // Contenteditable DIV
            const el = /** @type {HTMLElement} */ (this);
            const totalLen = (el.textContent || '').length;

            if (index < 0) index = 0;
            if (index > totalLen) index = totalLen;

            const sel = window.getSelection();
            if (!sel) return;

            const range = document.createRange();
            el.focus();

            // Empty element → ensure a text node to place the caret into
            if (totalLen === 0) {
                if (!el.firstChild) el.appendChild(document.createTextNode(''));
                // place at start
                range.setStart(el.firstChild, 0);
                range.collapse(true);
                sel.removeAllRanges();
                sel.addRange(range);
                return;
            }

            // If caret is at the very end, this is fastest/cleanest
            if (index === totalLen) {
                range.selectNodeContents(el);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
                return;
            }

            // Walk text nodes to find the node that contains the index-th character
            const walker = document.createTreeWalker(
                el,
                NodeFilter.SHOW_TEXT,
                {
                    acceptNode(node) {
                        // skip empty/whitespace-only nodes if you want; or just accept all text
                        return node.nodeValue ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                    }
                }
            );

            let pos = 0;
            let node = walker.nextNode();
            while (node) {
                const nextPos = pos + node.nodeValue.length;
                if (index <= nextPos) {
                    const offset = index - pos; // char offset within this text node
                    range.setStart(node, offset);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    return;
                }
                pos = nextPos;
                node = walker.nextNode();
            }

            // Fallback: collapse at end if something unexpected happened
            range.selectNodeContents(el);
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
        };

        /**
         * Methods to deal with different types of data
         */
        const parseMethods = {
            'FIND': function(v, a) {
                if (isBlank(this.values[this.index])) {
                    this.values[this.index] = '';
                }
                // TODO: tratar eventos
                if (this.event && this.event.inputType && this.event.inputType.indexOf('delete') > -1) {
                    this.values[this.index] += v;
                    return;
                }
                let pos = 0;
                let count = 0;
                let value = (this.values[this.index] + v).toLowerCase();
                for (let i = 0; i < a.length; i++) {
                    if (a[i].toLowerCase().indexOf(value) === 0) {
                        pos = i;
                        count++;
                    }
                }
                if (count > 1) {
                    this.values[this.index] += v;
                } else if (count === 1) {
                    // Jump a number of chars
                    let t = (a[pos].length - this.values[this.index].length) - 1;
                    this.position += t;
                    this.values[this.index] = a[pos];
                    this.index++;
                    return pos;
                }
            },
            'YEAR': function(v, s) {
                if (isBlank(this.values[this.index])) {
                    this.values[this.index] = '';
                }

                let number = parseInt(v);

                if (number >= 0 && number <= 10) {
                    if (this.values[this.index].length < s) {
                        this.values[this.index] += v;
                    }
                }
                if (this.values[this.index].length === s) {
                    let y = new Date().getFullYear().toString();
                    if (s === 2) {
                        y = y.substring(0,2) + this.values[this.index];
                    } else if (s === 3) {
                        y = y.substring(0,1) + this.values[this.index];
                    } else if (s === 4) {
                        y = this.values[this.index];
                    }
                    this.date[0] = y;
                    this.index++;
                }
            },
            'YYYY': function(v) {
                parseMethods.YEAR.call(this, v, 4);
            },
            'YYY': function(v) {
                parseMethods.YEAR.call(this, v, 3);
            },
            'YY': function(v) {
                parseMethods.YEAR.call(this, v, 2);
            },
            'MMMMM': function(v) {
                if (isBlank(this.values[this.index])) {
                    this.values[this.index] = '';
                }
                let value = (this.values[this.index] + v).toLowerCase();
                for (var i = 0; i < monthsFull.length; i++) {
                    if (monthsFull[i][0].toLowerCase().indexOf(value) === 0) {
                        this.values[this.index] = monthsFull[i][0];
                        this.date[1] = i + 1;
                        this.index++;
                        break;
                    }
                }
            },
            'MMMM': function(v) {
                let ret = parseMethods.FIND.call(this, v, monthsFull);
                if (typeof(ret) !== 'undefined') {
                    this.date[1] = ret + 1;
                }
            },
            'MMM': function(v) {
                let ret = parseMethods.FIND.call(this, v, months);
                if (typeof(ret) !== 'undefined') {
                    this.date[1] = ret + 1;
                }
            },
            'MM': function(v, single) {
                const commit = () => {
                    this.date[1] = this.values[this.index];
                    this.index++;
                }

                let number = parseInt(v);

                if (isBlank(this.values[this.index])) {
                    if (number > 1 && number < 10) {
                        if (! single) {
                            v = '0' + v;
                        }
                        this.values[this.index] = v;
                        commit();
                    } else if (number < 2) {
                        this.values[this.index] = v;
                    }
                } else {
                    if (this.values[this.index] == 1 && number < 3) {
                        this.values[this.index] += v;
                        commit();
                    } else if (this.values[this.index] == 0 && number > 0 && number < 10) {
                        this.values[this.index] += v;
                        commit();
                    } else {
                        let test = parseInt(this.values[this.index]);
                        if (test > 0 && test <= 12) {
                            if (! single) {
                                test = '0' + test;
                            }
                            this.values[this.index] = test;
                            commit();
                            return false;
                        }
                    }
                }
            },
            'M': function(v) {
                return parseMethods['MM'].call(this, v, true);
            },
            'MONTH': function(v) {
                return parseMethods['MMMM'].call(this, v);
            },
            'MON': function(v) {
                return parseMethods['MMM'].call(this, v);
            },
            'DDDD': function(v) {
                return parseMethods.FIND.call(this, v, weekDaysFull);
            },
            'DDD': function(v) {
                return parseMethods.FIND.call(this, v, weekDays);
            },
            'DD': function(v, single) {
                const commit = () => {
                    this.date[2] = this.values[this.index];
                    this.index++;
                }

                let number = parseInt(v);

                if (isBlank(this.values[this.index])) {
                    if (number > 3 && number < 10) {
                        if (! single) {
                            v = '0' + v;
                        }
                        this.values[this.index] = v;
                        commit();
                    } else if (number < 10) {
                        this.values[this.index] = v;
                    }
                } else {
                    if (this.values[this.index] == 3 && number < 2) {
                        this.values[this.index] += v;
                        commit();
                    } else if ((this.values[this.index] == 1 || this.values[this.index] == 2) && number < 10) {
                        this.values[this.index] += v;
                        commit();
                    } else if (this.values[this.index] == 0 && number > 0 && number < 10) {
                        this.values[this.index] += v;
                        commit();
                    } else {
                        let test = parseInt(this.values[this.index]);
                        if (test > 0 && test <= 31) {
                            if (! single) {
                                test = '0' + test;
                            }
                            this.values[this.index] = test;
                            commit();
                            return false;
                        }
                    }
                }
            },
            'D': function(v) {
                return parseMethods['DD'].call(this, v, true);
            },
            'DY': function(v) {
                return parseMethods['DDD'].call(this, v);
            },
            'DAY': function(v) {
                return parseMethods['DDDD'].call(this, v);
            },
            'HH12': function(v, two) {
                let test = false;

                let number = parseInt(v);

                if (isBlank(this.values[this.index])) {
                    if (number > 1 && number < 10) {
                        if (two) {
                            v = 0 + v;
                        }
                        this.date[3] = this.values[this.index] = v;
                        this.index++;
                    } else if (number < 10) {
                        this.values[this.index] = v;
                    }
                } else {
                    if (this.values[this.index] == 1 && number < 3) {
                        this.date[3] = this.values[this.index] += v;
                        this.index++;
                    } else if (this.values[this.index] < 1 && number < 10) {
                        this.date[3] = this.values[this.index] += v;
                        this.index++;
                    } else {
                        test = true;
                    }
                }

                // Re-test
                if (test === true) {
                    var t = parseInt(this.values[this.index]);
                    if (t >= 0 && t <= 12) {
                        this.date[3] = this.values[this.index];
                        this.index++;
                        return false;
                    }
                }
            },
            'HH24': function(v, two) {
                let test = false;

                let number = parseInt(v)

                if (number >= 0 && number < 10) {
                    if (isBlank(this.values[this.index])) {
                        if (number > 2 && number < 10) {
                            if (two) {
                                v = 0 + v;
                            }
                            this.date[3] = this.values[this.index] = v;
                            this.index++;
                        } else if (number < 10) {
                            this.values[this.index] = v;
                        }
                    } else {
                        if (this.values[this.index] == 2 && number < 4) {
                            if (! two && this.values[this.index] === '0') {
                                this.values[this.index] = '';
                            }
                            this.date[3] = this.values[this.index] += v;
                            this.index++;
                        } else if (this.values[this.index] < 2 && number < 10) {
                            if (! two && this.values[this.index] === '0') {
                                this.values[this.index] = '';
                            }
                            this.date[3] = this.values[this.index] += v;
                            this.index++;
                        } else {
                            test = true;
                        }
                    }
                } else {
                    test = true;
                }

                // Re-test
                if (test === true) {
                    var t = parseInt(this.values[this.index]);
                    if (t >= 0 && t < 24) {
                        this.date[3] = this.values[this.index];
                        this.index++;
                        return false;
                    }
                }
            },
            'HH': function(v) {
                parseMethods['HH24'].call(this, v, 1);
            },
            'H': function(v) {
                parseMethods['HH24'].call(this, v, 0);
            },
            '\\[H\\]': function(v) {
                if (this.values[this.index] == undefined) {
                    this.values[this.index] = '';
                }
                if (v.match(/[0-9]/g)) {
                    this.date[3] = this.values[this.index] += v;
                } else {
                    if (this.values[this.index].match(/[0-9]/g)) {
                        this.date[3] = this.values[this.index];
                        this.index++;
                        return false;
                    }
                }
            },
            'N60': function(v, i, two) {
                let test = false;

                let number = parseInt(v);

                if (number >= 0 && number < 10) {
                    if (isBlank(this.values[this.index])) {
                        if (number > 5 && number < 10) {
                            if (two) {
                                v = '0' + v;
                            }
                            this.date[i] = this.values[this.index] = v;
                            this.index++;
                        } else if (number < 10) {
                            this.values[this.index] = v;
                        }
                    } else {
                        if (this.values[this.index] < 6 && number < 10) {
                            if (! two && this.values[this.index] === '0') {
                                this.values[this.index] = '';
                            }
                            this.date[i] = this.values[this.index] += v;
                            this.index++;
                        } else {
                            test = true;
                        }
                    }
                } else {
                    test = true;
                }

                // Re-test
                if (test === true) {
                    var t = parseInt(this.values[this.index]);
                    if (t >= 0 && t < 60) {
                        this.date[i] = this.values[this.index];
                        this.index++;
                        return false;
                    }
                }
            },
            'MI': function(v) {
                parseMethods.N60.call(this, v, 4, true);
            },
            'SS': function(v) {
                parseMethods.N60.call(this, v, 5, true);
            },
            'I': function(v) {
                parseMethods.N60.call(this, v, 4, false);
            },
            'S': function(v) {
                parseMethods.N60.call(this, v, 5, false);
            },
            'AM/PM': function(v) {
                if (typeof(this.values[this.index]) === 'undefined') {
                    this.values[this.index] = '';
                }

                if (this.values[this.index] === '') {
                    if (v.match(/a/i) && this.date[3] < 13) {
                        this.values[this.index] += 'A';
                    } else if (v.match(/p/i)) {
                        this.values[this.index] += 'P';
                    }
                } else if (this.values[this.index] === 'A' || this.values[this.index] === 'P') {
                    this.values[this.index] += 'M';
                    this.index++;
                }
            },
            'WD': function(v) {
                if (typeof(this.values[this.index]) === 'undefined') {
                    this.values[this.index] = '';
                }

                let number = parseInt(v);

                if (number >= 0 && number < 7) {
                    this.values[this.index] = v;
                }
                if (this.values[this.index].length == 1) {
                    this.index++;
                }
            },
            // Numeric Methods
            '[0#]+([.,]{1}0*#*)?': function(v) {
                if (v === '.' && inputIsANumber(this.raw)) {
                    v = this.decimal;
                }

                if (isBlank(this.values[this.index])) {
                    this.values[this.index] = '';
                }

                if (v === '-') {
                    // Transform the number into negative if it is not already
                    if (this.values[this.index][0] != '-') {
                        this.values[this.index] = '-' + this.values[this.index];
                    }
                } else if (v === '+') {
                    // Transform the number into positive if it is negative
                    if (this.values[this.index][0] == '-') {
                        this.values[this.index] = this.values[this.index].replace('-', '');
                    }
                } else if (v == '0') {
                    // Only adds zero if there's a non-zero number before
                    if (this.values[this.index] != '0' && this.values[this.index] != '-0') {
                        this.values[this.index] += v;
                    }
                } else if (v > 0 && v < 10) {
                    // Verify if there's a zero to remove it, avoiding left zeros
                    if (this.values[this.index] == '0' || this.values[this.index] == '-0') {
                        this.values[this.index] = this.values[this.index].replace('0', '');
                    }
                    this.values[this.index] += v;
                } else if (v === this.decimal) {
                    // Only adds decimal when there's a number value on its left
                    if (! this.values[this.index].includes(this.decimal)) {
                        if (! this.values[this.index].replace('-', '').length) {
                            this.values[this.index] += '0';
                        }
                        this.values[this.index] += this.decimal;
                    }
                }
            },
            '[0#]+([.,]{1}0*#*)?%': function(v) {
                parseMethods['[0#]+([.,]{1}0*#*)?'].call(this, v);

                // Adds the % only if it has a number value
                if (this.values[this.index].match(/[\-0-9]/g)) {
                    if (this.values[this.index].indexOf('%') !== -1) {
                        this.values[this.index] = this.values[this.index].replaceAll('%', '');
                    }
                    this.values[this.index] += '%';
                } else {
                    this.values[this.index] = '';
                }
            },
            '#(.{1})##0?(.{1}0+)?( ?;(.*)?)?': function(v) {
                // Process first the number
                parseMethods['[0#]+([.,]{1}0*#*)?'].call(this, v, true);
                // Create the separators
                let separator = this.tokens[this.index].substring(1,2);


                let currentValue = this.values[this.index];
                // Remove existing separators and negative sign
                currentValue = currentValue.replaceAll(separator, '');
                // Process separators
                let val = currentValue.split(this.decimal);
                if (val[0].length > 3) {
                    let number = [];
                    let count = 0;
                    for (var j = val[0].length - 1; j >= 0 ; j--) {
                        let c = val[0][j];
                        if (c >= 0 && c <= 9) {
                            if (count && ! (count % 3)) {
                                number.unshift(separator);
                            }
                            count++;
                        }
                        number.unshift(c);
                    }
                    val[0] = number.join('');
                }
                // Reconstruct the value
                this.values[this.index] = val.join(this.decimal);
            },
            '[0#]+([.,]{1}0*#*)?E{1}\\+0+': function(v) {
                parseMethods['[0#]+([.,]{1}0*#*)?'].call(this, v);
            },
            '#{0,1}.*?\\?+\\/[0-9?]+': function (v) {
                if (isBlank(this.values[this.index])) {
                    this.values[this.index] = '';
                }

                const token = this.tokens[this.index]; // e.g. "# ?/?", "?/2", "# ??/16"
                let cur = this.values[this.index];

                // Parse RHS of mask to decide denominator rule
                const rhsRaw = (token.split('/')[1] || '').replace(/\s+/g, '');
                const allowDen = /^\d+$/.test(rhsRaw) ? rhsRaw : /^\?+$/.test(rhsRaw) ? '?' : '?';

                // ----- NEW: allow '-' as first char -----
                if (v === '-') {
                    if (cur.length === 0) {
                        this.values[this.index] = '-';
                    }
                    return; // never return false
                }
                // ----------------------------------------

                // Only accept digits / space / slash; ignore everything else
                if (!(/[0-9\/ ]/.test(v))) {
                    return;
                }

                // If we already have a slash and denominator is fixed but not yet appended,
                // auto-complete immediately regardless of what the user typed now.
                const hasSlashNow = cur.includes('/');
                if (hasSlashNow && allowDen !== '?') {
                    const afterSlash = cur.slice(cur.indexOf('/') + 1);
                    if (afterSlash.length === 0) {
                        this.values[this.index] = cur + allowDen;
                        this.index++; // move to next token
                        return;
                    }
                }

                // Empty -> only digits (or a leading '-' handled above)
                if (cur.length === 0) {
                    if (/\d/.test(v)) this.values[this.index] = v;
                    return;
                }

                const hasSpace = cur.includes(' ');
                const hasSlash = cur.includes('/');
                const last = cur[cur.length - 1];

                // Space rules: only one, must be before slash, must follow a digit
                if (v === ' ') {
                    if (!hasSpace && !hasSlash && /\d/.test(last)) {
                        this.values[this.index] = cur + ' ';
                    }
                    return;
                }

                // Slash rules: only one slash, not right after a space, must follow a digit
                if (v === '/') {
                    if (!hasSlash && last !== ' ' && /\d/.test(last)) {
                        if (allowDen === '?') {
                            this.values[this.index] = cur + '/';
                        } else {
                            this.values[this.index] = cur + '/' + allowDen;
                            this.index++; // conclude this token
                        }
                    }
                    return;
                }

                // Digit rules
                if (/\d/.test(v)) {
                    if (!hasSlash) {
                        // Before slash: digits always fine
                        this.values[this.index] = cur + v;
                        return;
                    }

                    // After slash
                    if (allowDen === '?') {
                        this.values[this.index] = cur + v;
                        return;
                    }

                    // Fixed denominator: enforce prefix and advance when complete
                    const afterSlash = cur.slice(cur.indexOf('/') + 1);
                    const nextDen = afterSlash + v;
                    if (allowDen.startsWith(nextDen)) {
                        this.values[this.index] = cur + v;
                        if (nextDen.length === allowDen.length) {
                            this.index++;
                        }
                    }
                }
            },
            '[a-zA-Z\\$]+': function(v) {
                // Token to be added to the value
                let word = this.tokens[this.index];
                // Value
                if (typeof(this.values[this.index]) === 'undefined') {
                    this.values[this.index] = '';
                }
                if (v === null) {
                    let size = this.values[this.index].length;
                    v = word.substring(size, size+1);
                }
                // Add the value
                this.values[this.index] += v;
                // Only if caret is before the change
                let current = this.values[this.index];
                // Add token to the values
                if (current !== word.substring(0,current.length)) {
                    this.values[this.index] = word;
                    // Next token to process
                    this.index++;
                    return false;
                } else if (current === word) {
                    // Next token to process
                    this.index++;
                }
            },
            'A': function(v) {
                return parseMethods['[a-zA-Z\\$]+'].call(this, v);
            },
            'a': function(v) {
                return parseMethods['[a-zA-Z\\$]+'].call(this, v);
            },
            '.': function(v) {
                return parseMethods['[a-zA-Z\\$]+'].call(this, v);
            },
            '&': function(v) {
                if (v.match(/^[a-zA-Z ]+$/)) {
                    this.values[this.index] = v;
                    this.index++;
                }
            },
            '\\*': function() {
                this.values[this.index] = '';
                this.index++;
                return false;
            },
            'C': function(v) {
                parseMethods['&'].call(this, v);
            },
            // General Methods
            '0': function(v) {
                if (v.match(/[0-9]/g)) {
                    this.values[this.index] = v;
                    this.index++;
                }
            },
            '9': function(v) {
                parseMethods['0'].call(this, v);
            },
            '#': function(v) {
                parseMethods['0'].call(this, v);
            },
            'L': function(v) {
                if (v.match(/[a-zA-Z]/gi)) {
                    this.values[this.index] = v;
                    this.index++;
                }
            },
            '\\?': function(v) {
                if (v.match(/[1-9]/g)) {
                    this.values[this.index] = v;
                    this.index++;
                }
            },
            '@': function(v) {
                if (isBlank(this.values[this.index])) {
                    this.values[this.index] = '';
                }
                this.values[this.index] += v;
            },
            '_[.\\s\\S]': function() {
                this.values[this.index] = ' ';
                this.index++;
                return false;
            },
            '\\(': function() {
                if (this.type === 'currency' && this.parenthesisForNegativeNumbers) {
                    this.values[this.index] = '';
                } else {
                    this.values[this.index] = '(';
                }
                this.index++;
                return false;
            },
            '\\)': function() {
                if (this.type === 'currency' && this.parenthesisForNegativeNumbers) {
                    this.values[this.index] = '';
                } else {
                    this.values[this.index] = ')';
                }
                this.index++;
                return false;
            },
            ',,M': function() {
                this.values[this.index] = 'M';
                this.index++;
                return false;
            },
            ',,,B': function() {
                this.values[this.index] = 'B';
                this.index++;
                return false;
            },
            '\\\\[.\\s\\S]': function(v) {
                this.values[this.index] = this.tokens[this.index].replace('\\', '');
                this.index++;
                return false;
            }
        }

        const extractDate = function() {
            let v = '';
            if (! (this.date[0] && this.date[1] && this.date[2]) && (this.date[3] || this.date[4])) {
                if (this.mask.toLowerCase().indexOf('[h]') !== -1) {
                    v = parseInt(this.date[3]);
                } else {
                    let h = parseInt(this.date[3]);
                    if (h < 13 && this.values.indexOf('PM') !== -1) {
                        v = (h+12) % 24;
                    } else {
                        v = h % 24;
                    }
                }
                if (this.date[4]) {
                    v += parseFloat(this.date[4] / 60);
                }
                if (this.date[5]) {
                    v += parseFloat(this.date[5] / 3600);
                }
                v /= 24;
            } else if (this.date[0] || this.date[1] || this.date[2] || this.date[3] || this.date[4] || this.date[5]) {
                if (this.date[0] && this.date[1] && ! this.date[2]) {
                    this.date[2] = 1;
                }
                var t = Helpers.now(this.date);
                v = Helpers.dateToNum(t);
            }

            if (isNaN(v)) {
                v = '';
            }

            return v;
        }

        // Types TODO: Generate types so we can garantee that text,scientific, numeric,percentage, current are not duplicates. If they are, it will be general or broken.

        const getTokens = function(str) {
            // Check cache first - direct access, undefined check is fast
            let result = tokensCache[str];
            if (result !== undefined) {
                return result;
            }

            allExpressionsRegex.lastIndex = 0; // Reset for global regex
            result = str.match(allExpressionsRegex);
            tokensCache[str] = result;
            return result;
        }

        /**
         * Get the method of one given token
         */
        const getMethod = function(str, temporary) {
            str = str.toString().toUpperCase();

            // Check cache first - direct access, undefined check is fast
            let cached = methodCache[str];
            if (cached !== undefined) {
                return cached;
            }

            // Check for datetime mask
            const datetime = temporary.every(t => t.type === 'datetime' || t.type === 'general' || t.type === 'escape');

            // Use priority order for faster matching with pre-compiled regexes
            for (const type of tokenPriority) {
                if (!datetime && type === 'datetime') continue;

                for (const compiled of compiledTokens[type]) {
                    if (compiled.regex.test(str)) {
                        const result = { type: type, method: compiled.method };
                        methodCache[str] = result;
                        return result;
                    }
                }
            }
            methodCache[str] = null;
            return null;
        }

        const fixMinuteToken = function(t) {
            const len = t.length;
            for (let i = 0; i < len; i++) {
                const token = t[i];
                if (token === 'M' || token === 'MM') {
                    // Check if this M is a minute (near H or S) rather than month
                    let isMinute = false;

                    // Check previous 2 tokens for H (hour indicator)
                    if (i > 0) {
                        const prev1 = t[i - 1];
                        // Use includes for fast check - covers H, HH, HH24, HH12, [H], etc
                        if (prev1 && prev1.includes('H')) {
                            isMinute = true;
                        } else if (i > 1) {
                            const prev2 = t[i - 2];
                            if (prev2 && prev2.includes('H')) {
                                isMinute = true;
                            }
                        }
                    }

                    // Check next 2 tokens for S (seconds indicator) if not already determined
                    if (!isMinute && i < len - 1) {
                        const next1 = t[i + 1];
                        // Use includes for fast check - covers S, SS, MS, etc
                        if (next1 && next1.includes('S')) {
                            isMinute = true;
                        } else if (i < len - 2) {
                            const next2 = t[i + 2];
                            if (next2 && next2.includes('S')) {
                                isMinute = true;
                            }
                        }
                    }

                    if (isMinute) {
                        t[i] = token === 'M' ? 'I' : 'MI';
                    }
                }
            }
        }

        /**
         * Identify each method for each token
         */
        const getMethodsFromTokens = function(t) {
            // Uppercase
            t = t.map(v => {
                return v.toString().toUpperCase();
            });

            // Compatibility with Excel
            fixMinuteToken(t);

            let result = [];
            for (let i = 0; i < t.length; i++) {
                var m = getMethod(t[i], result);
                if (m) {
                    result.push(m);
                } else {
                    result.push(null);
                }
            }
            return result;
        }

        const getMethodByPosition = function(control) {
            let methodName;
            if (control.methods[control.index] && typeof(control.value[control.position]) !== 'undefined') {
                methodName = control.methods[control.index].method;
            }

            let m = parseMethods[methodName];
            if (typeof(m) === 'function') {
                return m;
            }

            return false;
        }

        const processPaddingZeros = function(token, value, decimal) {
            if (! value) {
                return value;
            }
            let m = token.split(decimal);
            let desiredNumOfPaddingZeros = m[0].match(/[0]+/g);
            if (desiredNumOfPaddingZeros && desiredNumOfPaddingZeros[0]) {
                desiredNumOfPaddingZeros = desiredNumOfPaddingZeros[0].length
                let v = value.toString().split(decimal);
                let len = v[0].length;
                if (desiredNumOfPaddingZeros > len) {
                    v[0] = v[0].padStart(desiredNumOfPaddingZeros, '0');
                    return v.join(decimal);
                }
            }
        }

        const processNumOfPaddingZeros = function(control) {
            let negativeSignal = false;
            control.methods.forEach((method, k) => {
                if (method) {
                    if (method.type === 'numeric' || method.type === 'percentage' || method.type === 'scientific') {
                        let ret = processPaddingZeros(control.tokens[k], control.values[k], control.decimal);
                        if (ret) {
                            control.values[k] = ret;
                        }
                    }

                    if (isNumeric(control.type) && control.parenthesisForNegativeNumbers === true) {
                        if (isNumeric(method.type)) {
                            if (control.values[k] && control.values[k].toString().includes('-')) {
                                control.values[k] = control.values[k].replace('-', '');

                                negativeSignal = true;
                            }
                        }
                    }
                }
            });


            if (isNumeric(control.type) && control.parenthesisForNegativeNumbers === true && negativeSignal) {
                control.methods.forEach((method, k) => {
                    if (! control.values[k] && control.tokens[k] === '(') {
                        control.values[k] = '(';
                    } else if (! control.values[k] && control.tokens[k] === ')') {
                        control.values[k] = ')';
                    }
                });
            }
        }

        const getValue = function(control) {
            let value = control.values.join('');
            if (isNumeric(control.type)) {
                if (value.indexOf('--') !== false) {
                    value = value.replace('--', '-');
                }
                if (Number(control.raw) < 0 && value.includes('-')) {
                    value = '-' + value.replace('-', '');
                }
            }
            return value;
        }

        const inputIsANumber = function(num) {
            if (typeof(num) === 'string') {
                num = num.trim();
            }
            return !isNaN(num) && num !== null && num !== '';
        }

        const getType = function(control) {
            // Mask type
            let type = 'general';
            // Process other types
            for (var i = 0; i < control.methods.length; i++) {
                let m = control.methods[i];
                if (m) {
                    let t = m.type;
                    if (t !== 'general' && t !== 'escape' && t !== type) {
                        if (type === 'general') {
                            type = t;
                        } else {
                            type = 'general';
                            break;
                        }
                    }
                }
            }
            return type;
        }

        const isNumber = function(num) {
            if (typeof(num) === 'string') {
                num = num.trim();
            }
            return !isNaN(num) && num !== null && num !== '';
        }

        // TODO, get negative mask automatically based on the input sign?

        const getConfig = function(config, value) {
            // Internal default control of the mask system
            const control = {
                // Mask options
                options: {},
                // New values for each token found
                values: [],
                // Token position
                index: 0,
                // Character position
                position: 0,
                // Date raw values
                date: [0,0,0,0,0,0],
                // Raw number for the numeric values
                number: 0,
            }

            if (typeof(value) === 'undefined' || value === null) {
                value = '';
            }

            // Value to be masked
            control.value = value.toString();
            control.raw = value;


            // Options defined by the user
            if (typeof(config) == 'string') {
                // Mask
                control.mask = config;
            } else if (config) {
                // Mask
                let k = Object.keys(config);
                for (var i = 0; i < k.length; i++) {
                    control[k[i]] = config[k[i]];
                }
            }

            // Controls of Excel that should be ignored
            let mask = control.mask;
            if (mask) {
                if (mask.indexOf(';') !== -1) {
                    let d = mask.split(';');

                    // Mask
                    mask = d[0];

                    if (typeof (value) === 'number' || isNumber(value)) {
                        if (Number(value) < 0 && d[1]) {
                            mask = d[1];
                        } else if (Number(value) === 0 && d[2]) {
                            mask = d[2];
                        } else {
                            mask = d[0];
                        }
                    } else {
                        if (typeof(d[3]) !== 'undefined') {
                            mask = d[3];
                        }
                    }
                }

                // Transform Excel locale patterns (e.g., [$$-409]#,##0.00) - only if pattern exists
                if (mask.indexOf('[$') !== -1) {
                    mask = transformExcelLocaleMask(mask);
                }

                // Cleaning the mask
                mask = cleanMask(mask, control);
                // Get only the first mask for now and remove
                control.mask = mask;
                // Get tokens which are the methods for parsing
                let tokens = control.tokens = getTokens(mask);
                // Get methods from the tokens
                control.methods = getMethodsFromTokens(tokens);
                // Type
                control.type = getType(control);
            }

            // Decimal only for numbers
            if (isNumeric(control.type) || control.locale) {
                control.decimal = getDecimal.call(control);
            }

            return control;
        }

        const toPlainString = function(num) {
            // Convert number to string if it isn't already
            num = String(num);

            // If it's not in exponential form, return as-is
            if (!/e/i.test(num)) return num;

            // Decompose scientific notation
            const [coefficient, exponent] = num.toLowerCase().split('e');
            const exp = parseInt(exponent, 10);

            // Handle sign
            const sign = coefficient[0] === '-' ? '-' : '';
            const [intPart, fracPart = ''] = coefficient.replace('-', '').split('.');

            const digits = intPart + fracPart;
            const decimalPos = intPart.length;

            let newPos = decimalPos + exp;

            if (newPos <= 0) {
                // Decimal point moves left
                return sign + '0.' + '0'.repeat(-newPos) + digits;
            } else if (newPos >= digits.length) {
                // Decimal point moves right, add trailing zeros
                return sign + digits + '0'.repeat(newPos - digits.length);
            } else {
                // Decimal point moves into the number
                return sign + digits.slice(0, newPos) + '.' + digits.slice(newPos);
            }
        };

        const adjustNumberOfDecimalPlaces = function(config, value) {
            let temp = value;
            let mask = config.mask;
            let expo;

            if (config.type === 'scientific') {
                mask = config.mask.toUpperCase().split('E')[0];

                let numOfDecimalPlaces = mask.split(config.decimal);
                numOfDecimalPlaces = numOfDecimalPlaces[1].match(/[0#]+/g);
                numOfDecimalPlaces = numOfDecimalPlaces[0]?.length ?? 0;
                temp = temp.toExponential(numOfDecimalPlaces);
                expo = temp.toString().split('e+');
                temp = Number(expo[0]);
            }

            if (mask.indexOf(config.decimal) === -1) {
                // No decimal places
                if (! Number.isInteger(temp)) {
                    temp = temp.toFixed(0);
                }
            } else {
                // Length of the decimal
                let mandatoryDecimalPlaces = mask.split(config.decimal);
                mandatoryDecimalPlaces = mandatoryDecimalPlaces[1].match(/0+/g);
                if (mandatoryDecimalPlaces) {
                    mandatoryDecimalPlaces = mandatoryDecimalPlaces[0].length;
                } else {
                    mandatoryDecimalPlaces = 0;
                }
                // Amount of decimal
                let numOfDecimalPlaces = temp.toString().split(config.decimal)
                numOfDecimalPlaces = numOfDecimalPlaces[1]?.length ?? 0;
                // Necessary adjustment
                let necessaryAdjustment = 0;
                if (numOfDecimalPlaces < mandatoryDecimalPlaces) {
                    necessaryAdjustment = mandatoryDecimalPlaces;
                } else {
                    // Optional
                    let optionalDecimalPlaces = mask.split(config.decimal);
                    optionalDecimalPlaces = optionalDecimalPlaces[1].match(/[0#]+/g);
                    if (optionalDecimalPlaces) {
                        optionalDecimalPlaces = optionalDecimalPlaces[0].length;
                        if (numOfDecimalPlaces > optionalDecimalPlaces) {
                            necessaryAdjustment = optionalDecimalPlaces;
                        }
                    }
                }
                // Adjust decimal numbers if applicable
                if (necessaryAdjustment) {
                    let t = temp.toFixed(necessaryAdjustment);
                    let n = temp.toString().split('.');
                    let fraction = n[1];
                    if (fraction && fraction.length > necessaryAdjustment && fraction[fraction.length - 1] === '5') {
                        t = parseFloat(n[0] + '.' + fraction + '1').toFixed(necessaryAdjustment);
                    }
                    temp = t;
                }
            }

            if (config.type === 'scientific') {
                let ret = processPaddingZeros(mask, temp, config.decimal);
                if (ret) {
                    temp = ret;
                }
                expo[0] = temp;

                mask = config.mask.toUpperCase().split('E+')[1];
                ret = processPaddingZeros(mask, expo[1], config.decimal);
                if (ret) {
                    expo[1] = ret;
                }

                temp = expo.join('e+');
            }

            return temp;
        }

        const formatFraction = function(value, mask) {
            let maxDenominator;
            let fixedDenominator = null;
            let allowWholeNumber = true;

            // Check for fixed denominator like # ?/8 or ?/8
            const fixed = mask.match(/\/(\d+)/);
            if (fixed) {
                fixedDenominator = parseInt(fixed[1], 10);
                maxDenominator = fixedDenominator;
            } else {
                // Determine based on question marks in mask
                const match = mask.match(/\?\/(\?+)/);
                if (match) {
                    maxDenominator = Math.pow(10, match[1].length) - 1;
                } else {
                    maxDenominator = 9; // Default for # ?/? or ?/?
                }
            }
            // Check if mask allows whole number (e.g., ?/? or ?/8 implies no whole number)
            allowWholeNumber = mask.includes('#');

            // If we have a fixed denominator, use it exactly (don't simplify)
            if (fixedDenominator) {
                const isNegative = value < 0;
                const absValue = Math.abs(value);
                const numerator = Math.round(absValue * fixedDenominator);

                // For masks like ?/8, always output as pure fraction (no whole number)
                if (!allowWholeNumber) {
                    return isNegative ? `-${numerator}/${fixedDenominator}` : `${numerator}/${fixedDenominator}`;
                }

                // For masks like # ?/8, allow whole number
                const whole = Math.floor(numerator / fixedDenominator);
                const remainder = numerator % fixedDenominator;
                if (remainder === 0) {
                    return isNegative ? `-${whole}` : `${whole}`;
                }
                if (whole === 0) {
                    return isNegative ? `-${numerator}/${fixedDenominator}` : `${numerator}/${fixedDenominator}`;
                }
                return isNegative ? `-${whole} ${remainder}/${fixedDenominator}` : `${whole} ${remainder}/${fixedDenominator}`;
            }

            // Use continued fractions algorithm for better approximation
            function continuedFraction(value, maxDenom) {
                if (value === 0) return [0, 1];
                let sign = value < 0 ? -1 : 1;
                value = Math.abs(value);
                let whole = Math.floor(value);
                let frac = value - whole;
                if (frac === 0) return [sign * whole, 1];

                let h1 = 1, h2 = 0;
                let k1 = 0, k2 = 1;
                let x = frac;
                while (k1 <= maxDenom) {
                    let a = Math.floor(x);
                    let h0 = a * h1 + h2;
                    let k0 = a * k1 + k2;
                    if (k0 > maxDenom) break;
                    h2 = h1; h1 = h0;
                    k2 = k1; k1 = k0;
                    if (Math.abs(x - a) < 1e-10) break;
                    x = 1 / (x - a);
                }

                // Add the whole part back only if allowed
                let finalNum = sign * (allowWholeNumber ? whole * k1 + h1 : Math.round(value * k1));
                let finalDen = k1;
                return [finalNum, finalDen];
            }

            const [numerator, denominator] = continuedFraction(value, maxDenominator);

            // Handle the result
            const isNegative = numerator < 0;
            const absNumerator = Math.abs(numerator);
            const whole = allowWholeNumber ? Math.floor(absNumerator / denominator) : 0;
            const remainder = absNumerator % denominator;
            const sign = isNegative ? '-' : '';

            if (remainder === 0) {
                return `${sign}${whole || 0}`;
            }
            if (whole === 0 || !allowWholeNumber) {
                return `${sign}${absNumerator}/${denominator}`;
            }
            return `${sign}${whole} ${remainder}/${denominator}`;
        }

        const extractDateAndTime = function(value) {
            value = value.toString().substring(0,19);
            let splitStr = (value.indexOf('T') !== -1) ? 'T' : ' ';
            value = value.split(splitStr);

            let y = null;
            let m = null;
            let d = null;
            let h = '0';
            let i = '0';
            let s = '0';

            if (! value[1]) {
                if (value[0].indexOf(':') !== -1) {
                    value[0] = value[0].split(':');
                    h = value[0][0];
                    i = value[0][1];
                    s = value[0][2];
                } else {
                    value[0] = value[0].split('-');
                    y = value[0][0];
                    m = value[0][1];
                    d = value[0][2];
                }
            } else {
                value[0] = value[0].split('-');
                y = value[0][0];
                m = value[0][1];
                d = value[0][2];

                value[1] = value[1].split(':');
                h = value[1][0];
                i = value[1][1];
                s = value[1][2];
            }

            return [y,m,d,h,i,s];
        }

        const format = function(str, config) {
            let ret = new Intl.NumberFormat(config.locale, config.options || {}).format(str);

            config.values.push(ret);
        }

        const Component = function(str, config, returnObject) {
            // Get configuration
            const control = getConfig(config, str);

            if (control.locale) {
                format(str, control);
            } else if (control.mask) {
                // Walk every character on the value
                let method;
                while (method = getMethodByPosition(control)) {
                    let char = control.value[control.position];
                    if (char === hiddenCaret) {
                        control.caret = {
                            index: control.index,
                            position: control.values[control.index]?.length ?? 0,
                        }
                        control.position++;
                    } else {
                        // Get the method name to handle the current token
                        let ret = method.call(control, char);
                        // Next position
                        if (ret !== false) {
                            control.position++;
                        }
                    }
                }

                // Move index
                if (control.methods[control.index]) {
                    let type = control.methods[control.index].type;
                    if (isNumeric(type) && control.methods[++control.index]) {
                        let next;
                        while (next = control.methods[control.index]) {
                            if (control.methods[control.index].type === 'general') {
                                let method = control.methods[control.index].method;
                                if (method && typeof(parseMethods[method]) === 'function') {
                                    parseMethods[method].call(control, null);
                                }
                            } else {
                                break;
                            }
                        }
                    }
                }
            }
            if (control.caret) {
                let index = control.caret.index;
                let position = control.caret.position;
                let value = control.values[index] ?? '';
                // Re-apply the caret to the original position
                control.values[index] = value.substring(0, position) + hiddenCaret + value.substring(position);
            }

            control.value = getValue(control);

            if (returnObject) {
                return control;
            } else {
                return control.value;
            }
        }

        // Helper: Compare rendered value to original input
        const testMask = function(mask, value, original) {
            const rendered = Component.render(value, { mask }, true);
            return rendered.replace(/\s/g, '') === original.replace(/\s/g, '');
        }

        const autoCastingFractions = function(value) {
            const fractionPattern = /^\s*(-?\d+\s+)?(-?\d+)\/(\d+)\s*$/;
            const fractionMatch = value.match(fractionPattern);
            if (fractionMatch) {
                const sign = value.trim().startsWith('-') ? -1 : 1;
                const whole = fractionMatch[1] ? Math.abs(parseInt(fractionMatch[1])) : 0;
                const numerator = Math.abs(parseInt(fractionMatch[2]));
                const denominator = parseInt(fractionMatch[3]);

                if (denominator === 0) return null;

                const decimalValue = sign * (whole + (numerator / denominator));

                // Determine the mask
                let mask;
                if ([2, 4, 8, 16, 32].includes(denominator)) {
                    mask = whole !== 0 ? `# ?/${denominator}` : `?/${denominator}`;
                } else if (denominator <= 9) {
                    mask = whole !== 0 ? '# ?/?' : '?/?';
                } else {
                    mask = whole !== 0 ? '# ??/??' : '??/??';
                }

                if (testMask(mask, decimalValue, value.trim())) {
                    return { mask, value: decimalValue, type: 'fraction', category: 'fraction' };
                }
            }
            return null;
        }

        const autoCastingPercent = function(value) {
            const percentPattern = /^\s*([+-]?\d+(?:[.,]\d+)?)%\s*$/;
            const percentMatch = value.match(percentPattern);
            if (percentMatch) {
                const rawNumber = percentMatch[1].replace(',', '.');
                const decimalValue = parseFloat(rawNumber) / 100;

                const decimalPart = rawNumber.split('.')[1];
                const decimalPlaces = decimalPart ? decimalPart.length : 0;
                const mask = decimalPlaces > 0 ? `0.${'0'.repeat(decimalPlaces)}%` : '0%';

                if (testMask(mask, decimalValue, value.trim())) {
                    return { mask: mask, value: decimalValue, type: 'percent', category: 'numeric' };
                }
            }
            return null;
        }

        const autoCastingDates = function(value) {
            if (!value || typeof value !== 'string') {
                return null;
            }

            // Smart pattern detection based on the structure of the string

            // 1. Analyze the structure to determine possible formats
            const analyzeStructure = function(str) {
                const patterns = [];

                // Check for date with forward slashes: XX/XX/XXXX or XX/XX/XX
                if (str.match(/^\d{1,2}\/\d{1,2}\/\d{2,4}$/)) {
                    const parts = str.split('/');
                    const p1 = parseInt(parts[0]);
                    const p2 = parseInt(parts[1]);
                    const p3 = parseInt(parts[2]);

                    // Determine likely format based on values
                    if (p1 <= 12 && p2 <= 31 && p2 > 12) {
                        // Likely mm/dd/yyyy
                        patterns.push('mm/dd/yyyy', 'mm/dd/yy', 'm/d/yyyy', 'm/d/yy');
                    } else if (p1 <= 31 && p2 <= 12 && p1 > 12) {
                        // Likely dd/mm/yyyy
                        patterns.push('dd/mm/yyyy', 'dd/mm/yy', 'd/m/yyyy', 'd/m/yy');
                    } else if (p1 <= 12 && p2 <= 12) {
                        // Ambiguous - could be either, use locale preference
                        if (userLocale.startsWith('en-US')) {
                            patterns.push('mm/dd/yyyy', 'dd/mm/yyyy', 'mm/dd/yy', 'dd/mm/yy');
                        } else {
                            patterns.push('dd/mm/yyyy', 'mm/dd/yyyy', 'dd/mm/yy', 'mm/dd/yy');
                        }
                    }

                    // Add variations
                    if (p3 < 100) {
                        patterns.push('dd/mm/yy', 'mm/dd/yy', 'd/m/yy', 'm/d/yy');
                    } else {
                        patterns.push('dd/mm/yyyy', 'mm/dd/yyyy', 'd/m/yyyy', 'm/d/yyyy');
                    }
                }

                // Check for date with dashes: XX-XX-XXXX
                else if (str.match(/^\d{1,2}-\d{1,2}-\d{2,4}$/)) {
                    const parts = str.split('-');
                    const p1 = parseInt(parts[0]);
                    const p2 = parseInt(parts[1]);

                    if (p1 <= 12 && p2 <= 31 && p2 > 12) {
                        patterns.push('mm-dd-yyyy', 'mm-dd-yy', 'm-d-yyyy', 'm-d-yy');
                    } else if (p1 <= 31 && p2 <= 12 && p1 > 12) {
                        patterns.push('dd-mm-yyyy', 'dd-mm-yy', 'd-m-yyyy', 'd-m-yy');
                    } else {
                        patterns.push('dd-mm-yyyy', 'mm-dd-yyyy', 'dd-mm-yy', 'mm-dd-yy');
                    }
                }

                // Check for ISO format: YYYY-MM-DD
                else if (str.match(/^\d{4}-\d{1,2}-\d{1,2}$/)) {
                    patterns.push('yyyy-mm-dd', 'yyyy-m-d');
                }

                // Check for format: YYYY/MM/DD
                else if (str.match(/^\d{4}\/\d{1,2}\/\d{1,2}$/)) {
                    patterns.push('yyyy/mm/dd', 'yyyy/m/d');
                }

                // Check for dates with month names
                else if (str.match(/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i)) {
                    // DD Mon YYYY or DD Month YYYY
                    if (str.match(/^\d{1,2}\s+\w+\s+\d{2,4}$/i)) {
                        patterns.push('dd mmm yyyy', 'dd mmmm yyyy', 'd mmm yyyy', 'd mmmm yyyy',
                            'dd mmm yy', 'dd mmmm yy', 'd mmm yy', 'd mmmm yy');
                    }
                    // Mon DD, YYYY or Month DD, YYYY
                    else if (str.match(/^\w+\s+\d{1,2},?\s+\d{2,4}$/i)) {
                        patterns.push('mmm dd, yyyy', 'mmmm dd, yyyy', 'mmm d, yyyy', 'mmmm d, yyyy',
                            'mmm dd yyyy', 'mmmm dd yyyy', 'mmm d yyyy', 'mmmm d yyyy');
                    }
                    // DD-Mon-YYYY
                    else if (str.match(/^\d{1,2}-\w+-\d{2,4}$/i)) {
                        patterns.push('dd-mmm-yyyy', 'dd-mmmm-yyyy', 'd-mmm-yyyy', 'd-mmmm-yyyy',
                            'dd-mmm-yy', 'dd-mmmm-yy', 'd-mmm-yy', 'd-mmmm-yy');
                    }
                }

                // Check for weekday formats
                else if (str.match(/^(mon|tue|wed|thu|fri|sat|sun)/i)) {
                    if (str.match(/^\w+,\s+\d{1,2}\s+\w+\s+\d{4}$/i)) {
                        patterns.push('ddd, dd mmm yyyy', 'ddd, d mmm yyyy',
                            'dddd, dd mmmm yyyy', 'dddd, d mmmm yyyy');
                    }
                }

                // Check for datetime formats
                else if (str.includes(' ') && str.match(/\d{1,2}:\d{2}/)) {
                    const parts = str.split(' ');
                    if (parts.length >= 2) {
                        const datePart = parts[0];
                        const timePart = parts.slice(1).join(' ');

                        // Determine date format
                        let dateMasks = [];
                        if (datePart.includes('/')) {
                            dateMasks = ['dd/mm/yyyy', 'mm/dd/yyyy', 'd/m/yyyy', 'm/d/yyyy'];
                        } else if (datePart.includes('-')) {
                            if (datePart.match(/^\d{4}-/)) {
                                dateMasks = ['yyyy-mm-dd', 'yyyy-m-d'];
                            } else {
                                dateMasks = ['dd-mm-yyyy', 'mm-dd-yyyy', 'd-m-yyyy', 'm-d-yyyy'];
                            }
                        }

                        // Determine time format
                        let timeMasks = [];
                        if (timePart.match(/\d{1,2}:\d{2}:\d{2}/)) {
                            timeMasks = ['hh:mm:ss', 'h:mm:ss'];
                        } else {
                            timeMasks = ['hh:mm', 'h:mm'];
                        }

                        // Add AM/PM variants if present
                        if (timePart.match(/[ap]m/i)) {
                            timeMasks = timeMasks.map(t => t + ' am/pm');
                        }

                        // Combine date and time masks
                        for (const dateMask of dateMasks) {
                            for (const timeMask of timeMasks) {
                                patterns.push(`${dateMask} ${timeMask}`);
                            }
                        }
                    }
                }

                // Check for time-only formats
                else if (str.match(/^\d{1,2}:\d{2}(:\d{2})?(\s*(am|pm))?$/i)) {
                    if (str.match(/:\d{2}:\d{2}/)) {
                        patterns.push('hh:mm:ss', 'h:mm:ss');
                        if (str.match(/[ap]m/i)) {
                            patterns.push('hh:mm:ss am/pm', 'h:mm:ss am/pm');
                        }
                    } else {
                        patterns.push('hh:mm', 'h:mm');
                        if (str.match(/[ap]m/i)) {
                            patterns.push('hh:mm am/pm', 'h:mm am/pm');
                        }
                    }
                }

                // Check for extended hour format [h]:mm:ss
                else if (str.match(/^\[?\d+\]?:\d{2}:\d{2}$/)) {
                    patterns.push('[h]:mm:ss');
                }

                return [...new Set(patterns)]; // Remove duplicates
            };

            // Get candidate masks based on the string structure
            const candidateMasks = analyzeStructure(value);

            // If no patterns detected, try some common formats as fallback
            if (candidateMasks.length === 0) {
                if (userLocale.startsWith('en-US')) {
                    candidateMasks.push(
                        'mm/dd/yyyy', 'mm-dd-yyyy', 'yyyy-mm-dd',
                        'mm/dd/yy', 'mm-dd-yy',
                        'hh:mm:ss', 'hh:mm', 'h:mm am/pm'
                    );
                } else {
                    candidateMasks.push(
                        'dd/mm/yyyy', 'dd-mm-yyyy', 'yyyy-mm-dd',
                        'dd/mm/yy', 'dd-mm-yy',
                        'hh:mm:ss', 'hh:mm', 'h:mm'
                    );
                }
            }

            // Try each candidate mask
            for (const mask of candidateMasks) {
                try {
                    // Use Component.extractDateFromString to parse the date
                    const isoDate = Component.extractDateFromString(value, mask);

                    if (isoDate && isoDate !== '') {
                        // Parse the ISO date string to components
                        const parts = isoDate.split(' ');
                        const dateParts = parts[0].split('-');
                        const timeParts = parts[1] ? parts[1].split(':') : ['0', '0', '0'];

                        const year = parseInt(dateParts[0]);
                        const month = parseInt(dateParts[1]);
                        const day = parseInt(dateParts[2]);
                        const hour = parseInt(timeParts[0]);
                        const minute = parseInt(timeParts[1]);
                        const second = parseInt(timeParts[2]);

                        // Validate the date components
                        if (year > 0 && month >= 1 && month <= 12 && day >= 1 && day <= 31 &&
                            hour >= 0 && hour < 24 && minute >= 0 && minute < 60 && second >= 0 && second < 60) {

                            // Convert to Excel serial number
                            const excelNumber = Helpers.dateToNum(isoDate);

                            // Verify by rendering back
                            const rendered = Component.render(excelNumber, { mask: mask }, true);

                            // Case-insensitive comparison for month names
                            if (rendered.toLowerCase() === value.toLowerCase()) {
                                return {
                                    mask: mask,
                                    value: excelNumber,
                                    type: 'date',
                                    category: 'datetime'
                                };
                            }
                        }
                    }
                } catch (e) {
                }
            }

            // No matching format found
            return null;
        };

        const autoCastingCurrency = function (input, filterDecimal) {
            if (typeof input !== 'string') return null;

            const str = input.trim();
            if (!str) return null;

            const len = str.length;
            let isNegative = false;
            let hasParens = false;
            let symbol = '';
            let numericPart = '';
            let letterBuffer = '';
            let firstCommaPos = -1;
            let lastCommaPos = -1;
            let firstDotPos = -1;
            let lastDotPos = -1;
            let commaCount = 0;
            let dotCount = 0;
            let hasInvalidChars = false;
            let hasCurrencySymbol = false;

            // Single pass through the string
            for (let i = 0; i < len; i++) {
                const char = str[i];

                // Check for negative signs and parentheses
                if (char === '-' && !numericPart) {
                    isNegative = true;
                    continue;
                }
                if (char === '(') {
                    hasParens = true;
                    isNegative = true;
                    continue;
                }
                if (char === ')') continue;

                // Skip whitespace
                if (char === ' ' || char === '\t') {
                    if (letterBuffer) {
                        letterBuffer += char;
                    }
                    continue;
                }

                // Currency symbols
                if (char === '$' || char === '€' || char === '£' || char === '¥' ||
                    char === '₹' || char === '₽' || char === '₩' || char === '₫' || char === '¢') {
                    hasCurrencySymbol = true;
                    // Validate letter buffer: max 2 letters before symbol
                    const trimmedBuffer = letterBuffer.trim();
                    if (trimmedBuffer.length > 2) {
                        return null;
                    }
                    if (letterBuffer) {
                        symbol = letterBuffer + char;
                        letterBuffer = '';
                    } else {
                        symbol = char;
                    }
                    // Check if next char is a space to include it in symbol
                    if (i + 1 < len && (str[i + 1] === ' ' || str[i + 1] === '\t')) {
                        symbol += ' ';
                        i++; // Skip the space
                    }
                    continue;
                }

                // Letters (only valid BEFORE currency symbol, max 2 letters)
                if ((char >= 'A' && char <= 'Z') || (char >= 'a' && char <= 'z')) {
                    // Letters after symbol or numeric part are invalid
                    if (hasCurrencySymbol || numericPart) {
                        return null;
                    }
                    letterBuffer += char;
                    continue;
                }

                // Digits
                if (char >= '0' && char <= '9') {
                    // Reject if we have letters but no currency symbol
                    if (letterBuffer && !hasCurrencySymbol) {
                        return null;
                    }
                    letterBuffer = '';
                    numericPart += char;
                    continue;
                }

                // Comma and dot separators
                if (char === ',') {
                    if (firstCommaPos === -1) firstCommaPos = numericPart.length;
                    lastCommaPos = numericPart.length;
                    commaCount++;
                    numericPart += char;
                    continue;
                }
                if (char === '.') {
                    if (firstDotPos === -1) firstDotPos = numericPart.length;
                    lastDotPos = numericPart.length;
                    dotCount++;
                    numericPart += char;
                    continue;
                }

                // Invalid character
                hasInvalidChars = true;
            }

            // Reject if no currency symbol was found
            if (!hasCurrencySymbol) {
                return null;
            }

            // Reject if there are any invalid characters
            if (hasInvalidChars) {
                return null;
            }

            // If no numeric part, reject
            if (!numericPart) return null;

            // Ensure numeric part contains at least one digit (not just separators)
            if (!/\d/.test(numericPart)) return null;

            // Infer decimal and group separators
            let decimal = '.';
            let group = ',';

            // If filterDecimal is provided, use it to determine separators
            if (filterDecimal) {
                decimal = filterDecimal;
                group = filterDecimal === ',' ? '.' : ',';

                // Validate that the input matches this interpretation
                if (commaCount > 0 && dotCount > 0) {
                    // Both present: check if filterDecimal matches the last one (which should be decimal)
                    const lastIsComma = lastCommaPos > lastDotPos;
                    if ((filterDecimal === ',' && !lastIsComma) || (filterDecimal === '.' && lastIsComma)) {
                        return null;
                    }
                } else if (dotCount === 1 && commaCount === 0) {
                    // Only one dot: if NOT followed by exactly 3 digits, it's a decimal separator
                    const afterDot = numericPart.substring(lastDotPos + 1);
                    if (afterDot.length !== 3) {
                        // It's a decimal separator, must match filterDecimal
                        if (filterDecimal !== '.') {
                            return null;
                        }
                    }
                } else if (commaCount === 1 && dotCount === 0) {
                    // Only one comma: if NOT followed by exactly 3 digits, it's a decimal separator
                    const afterComma = numericPart.substring(lastCommaPos + 1);
                    if (afterComma.length !== 3) {
                        // It's a decimal separator, must match filterDecimal
                        if (filterDecimal !== ',') {
                            return null;
                        }
                    }
                }
            } else {
                // Infer from the input pattern
                if (commaCount > 0 && dotCount > 0) {
                    // Both present: the one that appears last is decimal
                    if (lastCommaPos > lastDotPos) {
                        decimal = ',';
                        group = '.';
                    }
                } else if (dotCount === 1 && commaCount === 0) {
                    // Only one dot: check if it's followed by exactly 3 digits
                    const afterDot = numericPart.substring(lastDotPos + 1);
                    if (afterDot.length === 3) {
                        // Likely a thousands separator
                        decimal = ',';
                        group = '.';
                    }
                } else if (commaCount === 1 && dotCount === 0) {
                    // Only one comma: check if it's followed by exactly 3 digits
                    const afterComma = numericPart.substring(lastCommaPos + 1);
                    if (afterComma.length !== 3) {
                        // Likely a decimal separator
                        decimal = ',';
                        group = '.';
                    }
                }
            }

            // Normalize: remove group separator, convert decimal to '.'
            let normalized = '';
            for (let i = 0; i < numericPart.length; i++) {
                const char = numericPart[i];
                if (char === group) continue;
                if (char === decimal) {
                    normalized += '.';
                } else {
                    normalized += char;
                }
            }

            const parsed = parseFloat(normalized);
            if (isNaN(parsed)) return null;

            const finalValue = isNegative ? -parsed : parsed;

            // Build mask
            const dotPos = normalized.indexOf('.');
            const decimalPlaces = dotPos !== -1 ? normalized.length - dotPos - 1 : 0;
            const maskDecimal = decimalPlaces ? decimal + '0'.repeat(decimalPlaces) : '';
            const groupMask = '#' + group + '##0';
            const needsSpace = symbol && !symbol.endsWith(' ') && !symbol.endsWith('\t') && !hasParens;
            let mask = symbol + (needsSpace ? ' ' : '') + groupMask + maskDecimal;

            if (hasParens) {
                mask = `(${mask})`;
            }

            return {
                mask,
                value: finalValue,
                type: 'currency',
                category: 'numeric'
            };
        }

        const autoCastingNumber = function (input, filterDecimal) {
            // If you currently support numeric inputs directly, keep this:
            if (typeof input === 'number' && Number.isFinite(input)) {
                return { mask: '0', value: input, type: 'number', category: 'numeric' };
            }

            if (typeof input !== 'string') {
                return null;
            }

            const sRaw = input.trim();

            // Check for simple integers first (with optional sign)
            if (/^[+-]?\d+$/.test(sRaw)) {
                const sign = /^[+-]/.test(sRaw) ? sRaw[0] : '';
                const digitsClean = (sign ? sRaw.slice(1) : sRaw);
                const rawDigits = sign ? sRaw.slice(1) : sRaw;
                const m = rawDigits.match(/^0+/);
                const leadingZeros = m ? m[0].length : 0;
                const mask = leadingZeros > 0 ? '0'.repeat(rawDigits.length) : '0';
                const value = Number(sign + digitsClean);
                return { mask, value, type: 'number', category: 'numeric' };
            }

            // Check for formatted numbers with thousand separators (no letters, no symbols)
            // Examples: "1,000.25", "1.000,25", "-1,234.56"
            if (/^[+-]?[\d,.]+$/.test(sRaw)) {
                let isNegative = sRaw[0] === '-';
                let numStr = isNegative ? sRaw.slice(1) : sRaw;

                // Count separators
                const commaCount = (numStr.match(/,/g) || []).length;
                const dotCount = (numStr.match(/\./g) || []).length;

                // Must have at least one digit
                if (!/\d/.test(numStr)) return null;

                // Infer decimal and group separators
                let decimal = '.';
                let group = ',';

                const lastCommaPos = numStr.lastIndexOf(',');
                const lastDotPos = numStr.lastIndexOf('.');

                // If filterDecimal is provided, use it to determine separators
                if (filterDecimal) {
                    decimal = filterDecimal;
                    group = filterDecimal === ',' ? '.' : ',';

                    // Validate that the input matches this interpretation
                    if (commaCount > 0 && dotCount > 0) {
                        // Both present: check if filterDecimal matches the last one (which should be decimal)
                        const lastIsComma = lastCommaPos > lastDotPos;
                        if ((filterDecimal === ',' && !lastIsComma) || (filterDecimal === '.' && lastIsComma)) {
                            return null;
                        }
                    } else if (dotCount === 1 && commaCount === 0) {
                        // Only one dot: if NOT followed by exactly 3 digits, it's a decimal separator
                        const afterDot = numStr.substring(lastDotPos + 1);
                        if (afterDot.length !== 3 || /[,.]/.test(afterDot)) {
                            // It's a decimal separator, must match filterDecimal
                            if (filterDecimal !== '.') {
                                return null;
                            }
                        }
                    } else if (commaCount === 1 && dotCount === 0) {
                        // Only one comma: if NOT followed by exactly 3 digits, it's a decimal separator
                        const afterComma = numStr.substring(lastCommaPos + 1);
                        if (afterComma.length !== 3 || /[,.]/.test(afterComma)) {
                            // It's a decimal separator, must match filterDecimal
                            if (filterDecimal !== ',') {
                                return null;
                            }
                        }
                    }
                } else {
                    // Infer from the input pattern
                    if (commaCount > 0 && dotCount > 0) {
                        // Both present: the one that appears last is decimal
                        if (lastCommaPos > lastDotPos) {
                            decimal = ',';
                            group = '.';
                        }
                    } else if (dotCount === 1 && commaCount === 0) {
                        // Only one dot: check if it's followed by exactly 3 digits (thousands separator)
                        const afterDot = numStr.substring(lastDotPos + 1);
                        if (afterDot.length === 3 && !/[,.]/.test(afterDot)) {
                            decimal = ',';
                            group = '.';
                        }
                    } else if (commaCount === 1 && dotCount === 0) {
                        // Only one comma: check if it's NOT followed by exactly 3 digits (decimal separator)
                        const afterComma = numStr.substring(lastCommaPos + 1);
                        if (afterComma.length !== 3 || /[,.]/.test(afterComma)) {
                            decimal = ',';
                            group = '.';
                        }
                    }
                }

                // Check if group separator is actually used in the input
                const hasGroupSeparator = (group === ',' && commaCount > 1) || (group === '.' && dotCount > 1) ||
                    (group === ',' && decimal === '.' && commaCount > 0) ||
                    (group === '.' && decimal === ',' && dotCount > 0);

                // Normalize: remove group separator, convert decimal to '.'
                let normalized = numStr.replace(new RegExp('\\' + group, 'g'), '').replace(decimal, '.');
                const parsed = parseFloat(normalized);
                if (isNaN(parsed)) return null;

                const value = isNegative ? -parsed : parsed;

                // Build mask
                const dotPos = normalized.indexOf('.');
                const decimalPlaces = dotPos !== -1 ? normalized.length - dotPos - 1 : 0;
                const maskDecimal = decimalPlaces ? decimal + '0'.repeat(decimalPlaces) : '';
                const mask = (hasGroupSeparator ? '#' + group + '##0' : '0') + maskDecimal;

                return { mask, value, type: 'number', category: 'numeric' };
            }

            return null;
        };

        const autoCastingScientific = function(input) {
            if (typeof input !== 'string') return null;

            const original = input.trim();

            // Match scientific notation: 1e3, -2.5E-4, etc.
            const sciPattern = /^[-+]?\d*\.?\d+[eE][-+]?\d+$/;
            if (!sciPattern.test(original)) return null;

            const parsed = parseFloat(original);
            if (isNaN(parsed)) return null;

            // Extract parts to determine mask
            const [coefficient, exponent] = original.toLowerCase().split('e');
            const decimalPlaces = coefficient.includes('.') ? coefficient.split('.')[1].length : 0;
            const mask = `0${decimalPlaces ? '.' + '0'.repeat(decimalPlaces) : ''}E+00`;

            return {
                mask,
                value: parsed,
                type: 'scientific',
                category: 'scientific'
            };
        }

        const autoCastingTime = function (input) {
            if (typeof input !== 'string') return null;
            const original = input.trim();

            // hh:mm[:ss][ am/pm]
            const m = original.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*(am|pm))?$/i);
            if (!m) return null;

            let h = parseInt(m[1], 10);
            const i = parseInt(m[2], 10);
            const s = m[3] ? parseInt(m[3], 10) : 0;
            const mer = m[4] && m[4].toLowerCase();

            // basic range checks
            if (i > 59 || s > 59) return null;
            if (mer) {
                if (h < 1 || h > 12) return null;
                if (mer === 'pm' && h < 12) h += 12;
                if (mer === 'am' && h === 12) h = 0;
            } else {
                if (h > 23) return null;
            }

            // Excel serial for time-of-day = hours/24 + minutes/1440 + seconds/86400
            const excel = (h + i / 60 + s / 3600) / 24;

            // Build mask according to how user typed it
            const hourToken = m[1].length === 1 ? 'h' : 'hh';
            const base = s !== 0 || m[3] ? `${hourToken}:mm:ss` : `${hourToken}:mm`;
            const mask = mer ? `${base} am/pm` : base;

            // Verify we can render back exactly what the user typed
            if (testMask(mask, excel, original)) {            // uses Component.render under the hood
                return { mask: mask, value: excel, type: 'time', category: 'datetime' };
            }

            // Try alternate hour width if needed
            const altHour = hourToken === 'hh' ? 'h' : 'hh';
            const alt = mer
                ? `${altHour}${base.slice(hourToken.length)} am/pm`
                : `${altHour}${base.slice(hourToken.length)}`;

            if (testMask(alt, excel, original)) {
                return { mask: alt, value: excel, type: 'time', category: 'datetime' };
            }

            return null;
        };

        const ParseValue = function(v, config) {
            if (v === '') return '';

            const originalInput = '' + v;
            const decimal = config.decimal || '.';

            // Validate that the input looks like a reasonable number format before extracting digits
            // Reject strings that are clearly not intended to be numbers (e.g., "test123", "abc", etc.)
            const hasLetters = /[a-zA-Z]/.test(originalInput);
            const hasDigits = /[0-9]/.test(originalInput);

            if (hasLetters && hasDigits) {
                // Mixed letters and digits - check if it's a valid numeric format
                // Allow currency symbols, currency codes (3 letters), percentage, and separators

                // Remove all valid numeric characters and symbols
                let cleaned = originalInput.replace(/[\d\s.,\-+()]/g, ''); // Remove digits, spaces, separators, signs, parentheses
                cleaned = cleaned.replace(/[A-Z]{1,2}[€$£¥₹₽₩₫¢]/gi, ''); // Remove 1-2 letter prefix + currency symbol (R$, U$, etc.)
                cleaned = cleaned.replace(/[€$£¥₹₽₩₫¢]/g, ''); // Remove remaining currency symbols
                cleaned = cleaned.replace(/%/g, ''); // Remove percentage
                cleaned = cleaned.replace(/\b[A-Z]{3}\b/g, ''); // Remove 3-letter currency codes (USD, BRL, etc.)

                // If anything remains, it's likely invalid (like "test" in "test123")
                if (cleaned.trim().length > 0) {
                    return null; // Reject patterns like "test123", "abc123", etc.
                }
            }

            v = originalInput.split(decimal);

            // Detect negative sign
            let signal = v[0].includes('-');

            v[0] = v[0].match(/[0-9]+/g);
            if (v[0]) {
                if (signal) v[0].unshift('-');
                v[0] = v[0].join('');
            } else {
                v[0] = signal ? '-' : '';
            }

            if (v[1] !== undefined) {
                v[1] = v[1].match(/[0-9]+/g);
                v[1] = v[1] ? v[1].join('') : '';
            }

            return v[0] || v[1] ? v : '';
        }

        const Extract = function(v, config) {
            const parsed = ParseValue(v, config);
            if (parsed) {
                if (parsed[0] === '-') {
                    parsed[0] = '-0';
                }
                return parseFloat(parsed.join('.'));
            }
            return null;
        }

        /**
         * Try to get which mask that can transform the number in that format
         * @param {string|number} value - The value to detect the mask for
         * @param {string} [decimal] - Optional decimal separator filter ('.' or ',')
         */
        Component.autoCasting = function(value, decimal) {
            // Check cache first - use string value and decimal as key
            const cacheKey = decimal ? String(value) + '|' + decimal : String(value);
            let cached = autoCastingCache[cacheKey];
            if (cached !== undefined) {
                return cached;
            }

            const methods = [
                autoCastingDates,        // Most structured, the least ambiguous
                autoCastingTime,
                autoCastingFractions,    // Specific pattern with slashes
                autoCastingPercent,      // Recognizable with "%"
                autoCastingScientific,
                (v) => autoCastingNumber(v, decimal),       // Only picks up basic digits, decimals, leading 0s
                (v) => autoCastingCurrency(v, decimal),     // Complex formats, but recognizable
            ];

            let result = null;
            for (let method of methods) {
                const test = method(value);
                if (test) {
                    result = test;
                    break;
                }
            }

            // Cache the result (even if null)
            autoCastingCache[cacheKey] = result;
            return result;
        }

        Component.extract = function(value, options, returnObject) {
            if (! value || typeof options !== 'object') {
                return value;
            }

            if (options.locale) {
                const config = getConfig(options, value);
                config.value = Extract(value, config);
                if (value.toString().indexOf('%') !== -1) {
                    config.value /= 100;
                }
                return returnObject ? config : config.value;
            } else if (options.mask) {
                let mask = options.mask.split(';')[0];
                if (mask) {
                    options.mask = mask;
                }

                // Get decimal, group, type, etc.
                const config = getConfig(options, value);
                const type = config.type;

                let result;
                let o = options;

                if (type === 'text') {
                    result = value;
                } else if (type === 'general') {
                    result = Component(value, options);
                } else if (type === 'datetime') {
                    if (value instanceof Date) {
                        value = Component.getDateString(value, config.mask);
                    }

                    o = Component(value, options, true);

                    result = typeof o.value === 'number' ? o.value : extractDate.call(o);
                } else if (type === 'scientific') {
                    result = typeof value === 'string' ? Number(value) : value;
                } else if (type === 'fraction') {
                    // Parse a fraction string according to the mask (supports mixed "# ?/d" or simple "?/d")
                    const mask = config.mask;

                    // Detect fixed denominator (e.g. "# ?/16" or "?/8")
                    const fixedDenMatch = mask.match(/\/\s*(\d+)\s*$/);
                    const fixedDen = fixedDenMatch ? parseInt(fixedDenMatch[1], 10) : null;

                    // Whether a mask allows a whole part (e.g. "# ?/?")
                    const allowWhole = mask.includes('#');

                    let s = ('' + value).trim();
                    if (!s) {
                        result = null;
                    } else {
                        // Allow leading parentheses or '-' for negatives
                        let sign = 1;
                        if (/^\(.*\)$/.test(s)) {
                            sign = -1;
                            s = s.slice(1, -1).trim();
                        }
                        if (/^\s*-/.test(s)) {
                            sign = -1;
                            s = s.replace(/^\s*-/, '').trim();
                        }

                        let out = null;

                        if (s.includes('/')) {
                            // sign? (whole )? numerator / denominator
                            // Examples:
                            //  "1 1/2" => whole=1, num=1, den=2
                            //  "1/2"   => whole=undefined, num=1, den=2
                            const m = s.match(/^\s*(?:(\d+)\s+)?(\d+)\s*\/\s*(\d+)\s*$/);
                            if (m) {
                                const whole = allowWhole && m[1] ? parseInt(m[1], 10) : 0;
                                const num = parseInt(m[2], 10);
                                let den = parseInt(m[3], 10);

                                // If mask fixes the denominator, enforce it
                                if (fixedDen) den = fixedDen;

                                if (den !== 0) {
                                    out = sign * (whole + num / den);
                                }
                            }
                        } else {
                            // No slash → treats as a plain number (e.g., whole only)
                            const plain = Number(s.replace(',', '.'));
                            if (!Number.isNaN(plain)) {
                                out = sign * Math.abs(plain);
                            }
                        }

                        result = out;
                    }
                } else {
                    // Default fallback — numeric/currency/percent/etc.
                    result = Extract(value, config);
                    // Adjust percent
                    if (type === 'percentage' && ('' + value).indexOf('%') !== -1) {
                        result = result / 100;
                    }
                }

                o.value = result;

                if (!o.type && type) {
                    o.type = type;
                }

                return returnObject ? o : result;
            }

            return value;
        };

        Component.render = function(value, options, fullMask) {
            // Nothing to render
            if (value === '' || value === undefined || value === null) {
                return '';
            }

            // Config
            const config = getConfig(options, value);

            if (config.locale) {
                value = Component(value, options);
            } else if (config.mask) {
                // Percentage
                if (config.type === 'datetime') {
                    var t = Component.getDateString(value, config.mask);
                    if (t) {
                        value = t;
                    } else {
                        return '';
                    }
                } else if (config.type === 'text') {
                    // Parse number
                    if (typeof (value) === 'number') {
                        value = value.toString();
                    }
                } else {
                    if (config.type === 'percentage') {
                        if (typeof (value) === 'string' && value.indexOf('%') !== -1) {
                            value = value.replace('%', '');
                        } else {
                            value = adjustPrecision(Number(value) * 100);
                        }
                    } else {
                        if (config.mask.includes(',,M')) {
                            if (typeof (value) === 'string' && value.indexOf('M') !== -1) {
                                value = value.replace('M', '');
                            } else {
                                value = Number(value) / 1000000;
                            }
                        } else if (config.mask.includes(',,,B')) {
                            if (typeof (value) === 'string' && value.indexOf('B') !== -1) {
                                value = value.replace('B', '');
                            } else {
                                value = Number(value) / 1000000000;
                            }
                        }
                    }

                    if (typeof (value) === 'string' && isNumber(value)) {
                        value = Number(value);
                    }

                    if (typeof value === 'number') {
                        // Temporary value
                        let temp = value;

                        if (config.type === 'fraction') {
                            temp = formatFraction(value, config.mask);
                        } else {
                            if (fullMask) {
                                temp = adjustNumberOfDecimalPlaces(config, value);

                                if (config.type === 'scientific') {
                                    return temp;
                                }
                            }
                        }

                        value = toPlainString(temp);

                        if (config.decimal === ',') {
                            value = value.replace('.', config.decimal);
                        }
                    }
                }

                // Process mask
                let control = Component(value, options, true);
                // Complement render
                if (fullMask) {
                    processNumOfPaddingZeros(control);
                }

                value = getValue(control);

                // If numeric mask but no numbers in input, return empty
                if (isNumeric(control.type)) {
                    // Check if any numeric digit was actually extracted
                    const hasNumericValue = control.values.some(v => v && /\d/.test(v));
                    if (! hasNumericValue) {
                        value = '';
                    }
                }

                if (options.input && options.input.tagName) {
                    if (options.input.contentEditable) {
                        options.input.textContent = value;
                    } else {
                        options.input.value = value;
                    }
                    focus(options.input);
                }
            }

            return value;
        }

        // Helper to extract date from a string
        Component.extractDateFromString = function (date, format) {
            let o = Component(date, { mask: format }, true);

            // Check if in format Excel (Need difference with format date or type detected is numeric)
            if (date > 0 && Number(date) == date && (o.values.join("") !== o.value || o.type == "numeric")) {
                var d = new Date(Math.round((date - 25569) * 86400 * 1000));
                return d.getFullYear() + "-" + Helpers.two(d.getMonth()) + "-" + Helpers.two(d.getDate()) + ' 00:00:00';
            }

            let complete = false;

            if (o.values && o.values.length === o.tokens.length && o.values[o.values.length - 1].length >= o.tokens[o.tokens.length - 1].length) {
                complete = true;
            }

            if (o.date[0] && o.date[1] && (o.date[2] || complete)) {
                if (!o.date[2]) {
                    o.date[2] = 1;
                }

                return o.date[0] + '-' + Helpers.two(o.date[1]) + '-' + Helpers.two(o.date[2]) + ' ' + Helpers.two(o.date[3]) + ':' + Helpers.two(o.date[4]) + ':' + Helpers.two(o.date[5]);
            }

            return '';
        }

        // Tokens
        const dateTokens = ['DAY', 'WD', 'DDDD', 'DDD', 'DD', 'D', 'Q', 'HH24', 'HH12', 'HH', '\\[H\\]', 'H', 'AM/PM', 'MI', 'SS', 'MS', 'YYYY', 'YYY', 'YY', 'Y', 'MONTH', 'MON', 'MMMMM', 'MMMM', 'MMM', 'MM', 'M', '.'];
        // All date tokens
        const allDateTokens = dateTokens.join('|')

        Component.getDateString = function(value, options) {
            if (! options) {
                options = {};
            }

            // Labels
            let format;

            if (options && typeof(options) == 'object') {
                if (options.format) {
                    format = options.format;
                } else if (options.mask) {
                    format = options.mask;
                }
            } else {
                format = options;
            }

            if (! format) {
                format = 'YYYY-MM-DD';
            }

            format = format.toUpperCase();

            // Date instance
            if (value instanceof Date) {
                value = Helpers.now(value);
            } else if (isNumber(value)) {
                value = Helpers.numToDate(value);
            }


            // Expression to extract all tokens from the string
            let e = new RegExp(allDateTokens, 'gi');
            // Extract
            let t = format.match(e);

            // Compatibility with Excel
            fixMinuteToken(t);

            // Object
            const o = {
                tokens: t
            }

            // Value
            if (value) {
                try {
                    // Data
                    o.data = extractDateAndTime(value);

                    if (o.data[1] && o.data[1] > 12) {
                        throw new Error('Invalid date');
                    } else if (o.data[4] && o.data[4] > 59) {
                        throw new Error('Invalid date');
                    } else if (o.data[5] && o.data[5] > 59) {
                        throw new Error('Invalid date');
                    } else if (o.data[0] != null && o.data[1] != null) {
                        let day = new Date(o.data[0], o.data[1], 0).getDate();
                        if (o.data[2] > day) {
                            throw new Error('Invalid date');
                        }
                    }

                    // Value
                    o.value = [];

                    // Calendar instance
                    let calendar = new Date(o.data[0], o.data[1] - 1, o.data[2], o.data[3], o.data[4], o.data[5]);

                    if (o.data[0] === null && o.data[1] === null && o.data[2] === null) {
                        // Do nothing
                    } else {
                        if (isNaN(calendar.getTime())) {
                            throw new Error('Invalid date');
                        }
                    }

                    // Get method
                    const get = function (i) {
                        // Token
                        let t = this.tokens[i];

                        // Case token
                        let s = t.toUpperCase();
                        let v = null;

                        if (s === 'YYYY') {
                            v = this.data[0];
                        } else if (s === 'YYY') {
                            v = this.data[0];
                            if (v) {
                                v = v.substring(1, 4);
                            }
                        } else if (s === 'YY') {
                            v = this.data[0];
                            if (v) {
                                v = v.substring(2, 4);
                            }
                        } else if (s === 'Y') {
                            v = this.data[0];
                            if (v) {
                                v = v.substring(3, 4);
                            }
                        } else if (t === 'MON') {
                            v = Helpers.months[calendar.getMonth()];
                            if (v) {
                                v = v.substr(0, 3).toUpperCase();
                            }
                        } else if (t === 'mon') {
                            v = Helpers.months[calendar.getMonth()];
                            if (v) {
                                v = v.substr(0, 3).toLowerCase();
                            }
                        } else if (t === 'MONTH') {
                            v = Helpers.months[calendar.getMonth()];
                            if (v) {
                                v = v.toUpperCase();
                            }
                        } else if (t === 'month') {
                            v = Helpers.months[calendar.getMonth()];
                            if (v) {
                                v = v.toLowerCase();
                            }
                        } else if (s === 'MMMMM') {
                            v = Helpers.months[calendar.getMonth()];
                            if (v) {
                                v = v.substr(0, 1);
                            }
                        } else if (s === 'MMMM' || t === 'Month') {
                            v = Helpers.months[calendar.getMonth()];
                        } else if (s === 'MMM' || t == 'Mon') {
                            v = Helpers.months[calendar.getMonth()];
                            if (v) {
                                v = v.substr(0, 3);
                            }
                        } else if (s === 'MM') {
                            v = Helpers.two(this.data[1]);
                        } else if (s === 'M') {
                            v = calendar.getMonth() + 1;
                        } else if (t === 'DAY') {
                            v = Helpers.weekdays[calendar.getDay()];
                            if (v) {
                                v = v.toUpperCase();
                            }
                        } else if (t === 'day') {
                            v = Helpers.weekdays[calendar.getDay()];
                            if (v) {
                                v = v.toLowerCase();
                            }
                        } else if (s === 'DDDD' || t == 'Day') {
                            v = Helpers.weekdays[calendar.getDay()];
                        } else if (s === 'DDD') {
                            v = Helpers.weekdays[calendar.getDay()];
                            if (v) {
                                v = v.substr(0, 3);
                            }
                        } else if (s === 'DD') {
                            v = Helpers.two(this.data[2]);
                        } else if (s === 'D') {
                            v = parseInt(this.data[2]);
                        } else if (s === 'Q') {
                            v = Math.floor((calendar.getMonth() + 3) / 3);
                        } else if (s === 'HH24' || s === 'HH') {
                            v = this.data[3]%24;
                            if (this.tokens.indexOf('AM/PM') !== -1) {
                                if (v > 12) {
                                    v -= 12;
                                } else if (v == '0' || v == '00') {
                                    v = 12;
                                }
                            }
                            v = Helpers.two(v);
                        } else if (s === 'HH12') {
                            v = this.data[3]%24;
                            if (v > 12) {
                                v = Helpers.two(v - 12);
                            } else {
                                v = Helpers.two(v);
                            }
                        } else if (s === 'H') {
                            v = this.data[3]%24;
                            if (this.tokens.indexOf('AM/PM') !== -1) {
                                if (v > 12) {
                                    v -= 12;
                                } else if (v == '0' || v == '00') {
                                    v = 12;
                                }
                            }
                        } else if (s === '[H]') {
                            v = this.data[3];
                        } else if (s === 'MI') {
                            v = Helpers.two(this.data[4]);
                        } else if (s === 'I') {
                            v = parseInt(this.data[4]);
                        } else if (s === 'SS') {
                            v = Helpers.two(this.data[5]);
                        } else if (s === 'S') {
                            v = parseInt(this.data[5]);
                        } else if (s === 'MS') {
                            v = calendar.getMilliseconds();
                        } else if (s === 'AM/PM') {
                            if (this.data[3] >= 12) {
                                v = 'PM';
                            } else {
                                v = 'AM';
                            }
                        } else if (s === 'WD') {
                            v = Helpers.weekdays[calendar.getDay()];
                        }

                        if (v === null) {
                            this.value[i] = this.tokens[i];
                        } else {
                            this.value[i] = v;
                        }
                    }

                    for (let i = 0; i < o.tokens.length; i++) {
                        get.call(o, i);
                    }

                    value = o.value.join('');
                } catch (e) {
                    value = '';
                }
            }

            return value;
        }

        Component.getDate = function(value, format) {
            if (! format) {
                format = 'YYYY-MM-DD';
            }

            let ret = value;
            if (ret && Number(ret) == ret) {
                ret = Helpers.numToDate(ret);
            }

            // Try a formatted date
            if (! Helpers.isValidDateFormat(ret)) {
                let tmp = Component.extractDateFromString(ret, format);
                if (tmp) {
                    ret = tmp;
                }
            }

            return Component.getDateString(ret, format);
        }

        Component.oninput = function(e, mask) {
            // Element
            let element = e.target;
            // Property
            let property = 'value';
            // Get the value of the input
            if (element.tagName !== 'INPUT') {
                property = 'textContent';
            }
            // Value
            let value = element[property];
            // Get the mask
            if (! mask) {
                mask = element.getAttribute('data-mask');
            }
            // Keep the current caret position
            let caret = getCaret(element);
            if (caret) {
                value = value.substring(0, caret) + hiddenCaret + value.substring(caret);
            }

            // Run mask
            let result = Component(value, { mask: mask }, true);

            // New value
            let newValue = result.values.join('');
            // Apply the result back to the element
            if (newValue !== value && ! e.inputType.includes('delete')) {
                // Set the caret to the position before transformation
                let caret = newValue.indexOf(hiddenCaret);
                if (caret !== -1) {
                    // Apply value
                    element[property] = newValue.replace(hiddenCaret, "");
                    // Set caret
                    setCaret.call(element, caret);
                } else {
                    // Apply value
                    element[property] = newValue;
                    // Make sure the caret is positioned in the end
                    focus(element);
                }
            }
        }

        Component.getType = function(config) {
            // Get configuration
            const control = getConfig(config, null);

            return control.type;
        };

        Component.adjustPrecision = adjustPrecision;

        return Component;
    })();

    return { Mask: Mask, Helpers: Helpers };
})));

/***/ }),

/***/ 673:
/***/ (function(module, __unused_webpack_exports, __webpack_require__) {



if (! Modal && "function" === 'function') {
    var Modal = __webpack_require__(392);
}

if (! utils && "function" === 'function') {
    var utils = __webpack_require__(91);
}

const Helpers = utils.Helpers;
const Mask = utils.Mask;

; (function (global, factory) {
     true ? module.exports = factory() :
    0;
}(this, (function () {

    class CustomEvents extends Event {
        constructor(type, props, options) {
            super(type, {
                bubbles: true,
                composed: true,
                ...options,
            });

            if (props) {
                for (const key in props) {
                    // Avoid assigning if property already exists anywhere on `this`
                    if (! (key in this)) {
                        this[key] = props[key];
                    }
                }
            }
        }
    }

    // Dispatcher
    const Dispatch = function(method, type, options) {
        // Try calling the method directly if provided
        if (typeof method === 'function') {
            let a = Object.values(options);
            return method(...a);
        } else if (this.tagName) {
            this.dispatchEvent(new CustomEvents(type, options));
        }
    }

    // Translations
    const T = function(t) {
        if (typeof(document) !== "undefined" && document.dictionary) {
            return document.dictionary[t] || t;
        } else {
            return t;
        }
    }

    const filterData = function(year, month) {
        // Data for the month
        let data = {};
        if (Array.isArray(this.data)) {
            this.data.map(function (v) {
                if (!v || typeof v !== 'object' || typeof v.date !== 'string') {
                    return;
                }
                let d = year + '-' + Helpers.two(month + 1);
                if (v.date.substring(0, 7) === d) {
                    if (!data[v.date]) {
                        data[v.date] = [];
                    }
                    data[v.date].push(v);
                }
            });
        }
        return data;
    }

    // Get the short weekdays name
    const getWeekdays = function(firstDayOfWeek) {
        const reorderedWeekdays = [];
        for (let i = 0; i < 7; i++) {
            const dayIndex = (firstDayOfWeek + i) % 7;
            reorderedWeekdays.push(Helpers.weekdays[dayIndex]);
        }

        return reorderedWeekdays.map(w => {
            return { title: w.substring(0, 1) };
        });
    }

    const Views = function(self) {
        const view = {};

        // Create years container
        view.years = [];
        view.months = [];
        view.days = [];
        view.hours = [];
        view.minutes = [];

        for (let i = 0; i < 16; i++) {
            view.years.push({
                title: null,
                value: null,
                selected: false,
            });
        }

        for (let i = 0; i < 12; i++) {
            view.months.push({
                title: null,
                value: null,
                selected: false,
            });
        }

        for (let i = 0; i < 42; i++) {
            view.days.push({
                title: null,
                value: null,
                selected: false,
            });
        }

        for (let i = 0; i < 24; i++) {
            view.hours.push({
                title: Helpers.two(i),
                value: i
            });
        }

        for (let i = 0; i < 60; i++) {
            view.minutes.push({
                title: Helpers.two(i),
                value: i
            });
        }

        view.years.update = function(date) {
            let year = date.getUTCFullYear();
            let start = year - (year % 16);

            for (let i = 0; i < 16; i++) {
                let item = view.years[i];
                let value = start + i;

                item.title = value
                item.value = value;

                if (self.cursor.y === value) {
                    item.selected = true;
                    // Current item
                    self.cursor.current = item;
                } else {
                    item.selected = false;
                }
            }
        }

        view.months.update = function(date) {
            let year = date.getUTCFullYear();

            for (let i = 0; i < 12; i++) {
                let item = view.months[i];

                item.title = Helpers.months[i].substring(0,3);
                item.value = i;

                if (self.cursor.y === year && self.cursor.m === i) {
                    item.selected = true;
                    // Current item
                    self.cursor.current = item;
                } else {
                    item.selected = false;
                }
            }
        }

        view.days.update = function(date) {
            let year = date.getUTCFullYear();
            let month = date.getUTCMonth();
            let data = filterData.call(self, year, month);

            // First day
            let tmp = new Date(Date.UTC(year, month, 1, 0, 0, 0));
            let firstDayOfMonth = tmp.getUTCDay();
            let firstDayOfWeek = self.startingDay ?? 0;

            // Calculate offset based on desired first day of week. firstDayOfWeek: 0 = Sunday, 1 = Monday, 2 = Tuesday, etc.
            let offset = (firstDayOfMonth - firstDayOfWeek + 7) % 7;

            let index = -1 * offset;

            for (let i = 0; i < 42; i++) {
                index++;
                // Item
                let item = view.days[i];
                // Get the day
                tmp = new Date(Date.UTC(year, month, index, 0, 0, 0));
                // Day
                let day = tmp.getUTCDate();

                // Create the item
                item.title = day;
                item.value = index;
                item.number = Helpers.dateToNum(tmp.toISOString().substring(0, 10));

                // Reset range properties for each item
                item.start = false;
                item.end = false;
                item.range = false;
                item.last = false;
                item.disabled = false;
                item.data = null;

                // Check selections
                if (tmp.getUTCMonth() !== month) {
                    // Days are not in the current month
                    item.grey = true;
                } else {
                    // Check for data
                    let d = [ year, Helpers.two(month+1), Helpers.two(day) ].join('-');

                    if (data && data[d]) {
                        item.data = data[d];
                    }

                    item.grey = false;
                }
                // Month
                let m = tmp.getUTCMonth();

                // Select cursor
                if (self.cursor.y === year && self.cursor.m === m && self.cursor.d === day) {
                    item.selected = true;
                    // Current item
                    self.cursor.current = item;
                } else {
                    item.selected = false;
                }


                // Valid ranges
                if (self.validRange) {
                    if (typeof self.validRange === 'function') {
                        let ret = self.validRange(day,m,year,item);
                        if (typeof ret !== 'undefined') {
                            item.disabled = ret;
                        }
                    } else {
                        let current = year + '-' + Helpers.two(m+1) + '-' + Helpers.two(day);

                        let test1 = !self.validRange[0] || current >= self.validRange[0].substr(0, 10);
                        let test2 = !self.validRange[1] || current <= self.validRange[1].substr(0, 10);

                        if (! (test1 && test2)) {
                            item.disabled = true;
                        }
                    }
                }

                // Select range
                if (self.range && self.rangeValues) {
                    // Only mark start/end if the number matches
                    item.start = self.rangeValues[0] === item.number;
                    item.end = self.rangeValues[1] === item.number;
                    // Mark as part of range if between start and end
                    item.range = self.rangeValues[0] && self.rangeValues[1] && self.rangeValues[0] <= item.number && self.rangeValues[1] >= item.number;
                }
            }
        }

        return view;
    }

    const isTrue = function(v) {
        return v === true || v === 'true';
    }

    const isNumber = function (num) {
        if (typeof(num) === 'string') {
            num = num.trim();
        }
        return !isNaN(num) && num !== null && num !== '';
    }

    const Calendar = function(children, { onchange, onload, track }) {
        let self = this;

        // Event
        let change = self.onchange;
        self.onchange = null;

        // Coerce startingDay to a number so string inputs ('1') don't trigger string concat in modulo math
        if (typeof self.startingDay !== 'number') {
            self.startingDay = Number(self.startingDay) || 0;
        }

        // Weekdays
        self.weekdays = getWeekdays(self.startingDay);

        // Cursor
        self.cursor = {};

        // Time
        self.time = !! self.time;

        // Range values
        self.rangeValues = null;

        // Calendar date
        let date = new Date();

        // Views
        const views = Views(self);
        const hours = views.hours;
        const minutes = views.minutes;

        // Initial view
        self.view = 'days';

        // Auto Input
        if (self.input === 'auto') {
            self.input = document.createElement('input');
            self.input.type = 'text';
        }


        // Get the position of the data based on the view
        const getPosition = function() {
            let position = 2;
            if (self.view === 'years') {
                position = 0;
            } else if (self.view === 'months') {
                position = 1;
            }
            return position;
        }

        const setView = function(e) {
            if (typeof e === 'object') {
                e = this.getAttribute('data-view');
            }

            // Valid views
            const validViews = ['days', 'months', 'years'];

            // Define new view
            if (validViews.includes(e) && self.view !== e) {
                self.view = e;
            }
        }

        const reloadView = function(reset) {
            if (reset) {
                // Update options to the view
                self.options = views[self.view];
            }
            // Update the values of hte options of hte view
            views[self.view]?.update.call(self, date);
        }

        const getValue = function() {
            let value = null;
            if (isTrue(self.range)) {
                if (Array.isArray(self.rangeValues)) {
                    if (isTrue(self.numeric)) {
                        value = self.rangeValues;
                    } else {
                        value = [
                            Helpers.numToDate(self.rangeValues[0]).substring(0, 10),
                            Helpers.numToDate(self.rangeValues[1]).substring(0, 10)
                        ];
                    }
                }
            } else {
                value = getDate();
                if (isTrue(self.numeric)) {
                    value = Helpers.dateToNum(value);
                }
            }
            return value;
        }

        const setValue = function(v) {
            let d = new Date();
            if (v) {
                // Accept native Date objects by converting to ISO string
                if (v instanceof Date) {
                    v = v.toISOString().substring(0, 10);
                }
                if (isTrue(self.range)) {
                    if (v) {
                        if (! Array.isArray(v)) {
                            v = v.toString().split(',');
                        }
                        self.rangeValues = [...v];

                        if (v[0] && typeof (v[0]) === 'string' && v[0].indexOf('-')) {
                            self.rangeValues[0] = Helpers.dateToNum(v[0]);
                        }
                        if (v[1] && typeof (v[1]) === 'string' && v[1].indexOf('-')) {
                            self.rangeValues[1] = Helpers.dateToNum(v[1]);
                        }

                        v = v[0];
                    }
                } else if (typeof v === 'string' && v.includes(',')) {
                    v = v.split(',')[0];
                }

                if (v) {
                    v = isNumber(v) ? Helpers.numToDate(v) : v;
                    d = new Date(v + '  GMT+0');
                }

                // if no date is defined
                if (! Helpers.isValidDate(d)) {
                    d = new Date();
                }
            }

            // Update the internal calendar date
            setDate(d, true);
            // Update the view
            reloadView();
        }

        const getDate = function() {
            let v = [ self.cursor.y, self.cursor.m, self.cursor.d, self.hour, self.minute ];
            let d = new Date(Date.UTC(...v));
            // Update the headers of the calendar
            if (self.time) {
                return d.toISOString().substring(0, 19).replace('T', ' ');
            } else {
                return d.toISOString().substring(0, 10);
            }
        }

        const setDate = function(d, update) {
            if (Array.isArray(d)) {
                d = new Date(Date.UTC(...d));
            } else if (typeof(d) === 'string') {
                d = new Date(d);
            }

            // Update the date
            let value = d.toISOString().substring(0,10).split('-');
            let month = Helpers.months[parseInt(value[1])-1];
            let year = parseInt(value[0]);

            if (self.month !== month) {
                self.month = month;
            }
            if (self.year !== year) {
                self.year = year;
            }

            // Update the time
            let time = d.toISOString().substring(11,19).split(':');
            let hour = parseInt(time[0]);
            let minute = parseInt(time[1]);

            if (self.hour !== hour) {
                self.hour = hour;
            }
            if (self.minute !== minute) {
                self.minute = minute;
            }

            // Update internal date
            date = d;

            // Update cursor information
            if (update) {
                updateCursor();
            }
        }

        const updateCursor = function() {
            self.cursor.y = date.getUTCFullYear();
            self.cursor.m = date.getUTCMonth();
            self.cursor.d = date.getUTCDate();
        }

        const resetCursor = function() {
            // Remove selection from the current object
            let current = self.cursor.current;
            // Current item
            if (typeof current !== 'undefined') {
                current.selected = false;
            }
        }

        const setCursor = function(s) {
            // Reset current visual cursor
            resetCursor();
            // Update cursor based on the object position
            if (s) {
                // Update current
                self.cursor.current = s;
                // Update selected property
                s.selected = true;
            }

            updateCursor();

            // Update range
            if (isTrue(self.range)) {
                updateRange(s)
            }

            Dispatch.call(self, self.onupdate, 'update', {
                instance: self,
                value: date.toISOString(),
            });
        }

        const select = function(e, s) {
            if (self.disabled === true) {
                return;
            }
            // Get new date content
            let d = updateDate(s.value, getPosition());
            // New date
            setDate(new Date(Date.UTC(...d)))
            // Based where was the click
            if (self.view !== 'days') {
                // Back to the days
                self.view = 'days';
            } else if (! s.disabled) {
                if (isTrue(self.range)) {
                    // Start a new range
                    if (self.rangeValues && (self.rangeValues[0] >= s.number || self.rangeValues[1])) {
                        destroyRange();
                    }
                    // Range
                    s.range = true;
                    // Update range
                    if (! self.rangeValues) {
                        s.start = true;
                        self.rangeValues = [s.number, null];
                    } else {
                        s.end = true;
                        self.rangeValues[1] = s.number;
                    }
                    setCursor(s);
                } else {
                    setCursor(s);

                    update(e);
                }
            }
        }

        // Update Calendar
        const update = function(e) {
            self.setValue(getValue());

            if (! (e && e.type === 'click' && e.target.tagName === 'DIV' && self.time === true)) {
                self.close({ origin: 'button' });
            }
        }

        const reset = function() {
            self.setValue('');
            self.close({ origin: 'button' });
        }

        const updateDate = function(v, position) {
            // Current internal date
            let value = [date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(), self.hour, self.minute, 0];
            // Update internal date
            value[position] = v;
            // Return new value
            return value;
        }

        const move = function(direction) {
            // Reset visual cursor
            resetCursor();

            // Value
            let value;

            // Update the new internal date
            if (self.view === 'days') {
                // Select the new internal date
                value = updateDate(date.getUTCMonth()+direction, 1);
            } else if (self.view === 'months') {
                // Select the new internal date
                value = updateDate(date.getUTCFullYear()+direction, 0);
            } else if (self.view === 'years') {
                // Select the new internal date
                value = updateDate(date.getUTCFullYear()+(direction*16), 0);
            }

            // Update view
            setDate(value);

            // Reload content of the view
            reloadView();
        }

        const getJump = function(e) {
            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                return self.view === 'days' ? 7 : 4;
            }

            return 1;
        }

        const prev = function(e) {
            if (e && e.type === 'keydown') {
                // Current index
                let total = self.options.length;
                let position = self.options.indexOf(self.cursor.current) - getJump(e);
                if (position < 0) {
                    // Next month
                    move(-1);
                    // New position
                    position = total + position;
                }
                // Update cursor
                setCursor(self.options[position])
            } else {
                move(-1);
            }
        }

        const next = function(e) {
            if (e && e.type === 'keydown') {
                // Current index
                let total = self.options.length;
                let position = self.options.indexOf(self.cursor.current) + getJump(e);
                if (position >= total) {
                    // Next month
                    move(1);
                    // New position
                    position = position - total;
                }
                // Update cursor
                setCursor(self.options[position])
            } else {
                move(1);
            }
        }

        const getInput = function() {
            let input = self.input;
            if (input && input.current) {
                input = input.current;
            } else {
                if (self.input) {
                    input = self.input;
                }
            }

            return input;
        }

        const updateRange = function(s) {
            if (self.range && self.view === 'days' && self.rangeValues) {
                // Creating a range
                if (self.rangeValues[0] && ! self.rangeValues[1]) {
                    let number = s.number;
                    if (number) {
                        // Update range properties
                        for (let i = 0; i < self.options.length; i++) {
                            let v = self.options[i].number;
                            // Update property condition
                            self.options[i].range = v >= self.rangeValues[0] && v <= number;
                            self.options[i].last = (v === number);
                        }
                    }
                }
            }
        }

        const destroyRange = function() {
            if (self.range) {
                for (let i = 0; i < self.options.length; i++) {
                    if (self.options[i].range !== false) {
                        self.options[i].range = false;
                    }
                    if (self.options[i].start !== false) {
                        self.options[i].start = false;
                    }
                    if (self.options[i].end !== false) {
                        self.options[i].end = false;
                    }
                    if (self.options[i].last !== false) {
                        self.options[i].last = false;
                    }
                }
                self.rangeValues = null;
            }
        }

        const render = function(v) {
            if (v) {
                if (! Array.isArray(v)) {
                    v = v.toString().split(',');
                }

                v = v.map(entry => {
                    return Mask.render(entry, self.format || 'YYYY-MM-DD');
                }).join(',');
            }
            return v;
        }

        const normalize = function(v) {
            if (v instanceof Date) {
                v = Helpers.dateToString ? Helpers.dateToString(v) : v.toISOString().substring(0, 10);
            }
            if (! Array.isArray(v)) {
                v = v.toString().split(',');
            }

            return v.map(item => {
                if (item instanceof Date) {
                    return Helpers.dateToString ? Helpers.dateToString(item) : item.toISOString().substring(0, 10);
                }
                if (Number(item) == item) {
                    return Helpers.numToDate(item);
                } else {
                    if (Helpers.isValidDateFormat(item)) {
                        return item;
                    } else if (self.format) {
                        let tmp = Mask.extractDateFromString(item, self.format);
                        if (tmp) {
                            return tmp;
                        }
                    }
                }
            })
        }

        const extractValueFromInput = function() {
            let input = getInput();
            if (input) {
                let v;
                if (input.tagName === 'INPUT' || input.tagName === 'TEXTAREA') {
                    v = input.value;
                } else if (input.isContentEditable) {
                    v = input.textContent;
                }
                if (v) {
                    return normalize(v).join(',');
                }
                return v;
            }
        }

        const onopen = function() {
            let isEditable = false;
            let value = self.value;

            let input = getInput();
            if (input) {
                if (input.tagName === 'INPUT' || input.tagName === 'TEXTAREA') {
                    isEditable = !input.hasAttribute('readonly') && !input.hasAttribute('disabled');
                } else if (input.isContentEditable) {
                    isEditable = true;
                }

                let ret = extractValueFromInput();
                if (ret && ret !== value) {
                    value = ret;
                }
            }

            if (! isEditable) {
                self.content.focus();
            }

            // Update the internal date values
            setValue(value);

            // Open event
            Dispatch.call(self, self.onopen, 'open', {
                instance: self
            });
        }

        const onclose = function(modal, origin) {
            // Cancel range events
            destroyRange();
            // Close event
            Dispatch.call(self, self.onclose, 'close', {
                instance: self,
                origin: origin,
            });
        }

        const dispatchOnChangeEvent = function() {
            // Destroy range
            destroyRange();
            // Update the internal controllers
            setValue(self.value);
            // Events
            Dispatch.call(self, change, 'change', {
                instance: self,
                value: self.value,
            });
            // Update input
            let input = getInput();
            if (input) {
                // Update input value
                input.value = render(self.value);
                // Dispatch event
                Dispatch.call(input, null, 'change', {
                    instance: self,
                    value: self.value,
                });
            }
        }

        const events = {
            focusin: (e) => {
                if (self.modal && self.isClosed()) {
                    self.open();
                }
            },
            focusout: (e) => {
                if (self.modal && ! self.isClosed()) {
                    if (! (e.relatedTarget && self.modal.el.contains(e.relatedTarget))) {
                        self.modal.close({ origin: 'focusout' });
                    }
                }
            },
            click: (e) => {
                if (e.target.classList.contains('lm-calendar-input')) {
                    self.open();
                }
            },
            keydown: (e) => {
                if (self.modal) {
                    if (e.code === 'ArrowUp' || e.code === 'ArrowDown') {
                        if (! self.isClosed()) {
                            self.content.focus();
                        } else {
                            self.open();
                        }
                    } else if (e.code === 'Enter') {
                        if (! self.isClosed()) {
                            update(e);
                        } else {
                            self.open();
                        }
                    } else if (e.code === 'Escape') {
                        if (! self.isClosed()) {
                            self.modal.close({origin: 'escape'});
                        }
                    }
                }
            },
            input: (e) => {
                let input = e.target;
                if (input.classList.contains('lm-calendar-input')) {
                    if (! isTrue(self.range)) {
                        // TODO: process with range
                        // Apply mask
                        if (self.format) {
                            Mask.oninput(e, self.format);
                        }
                        let value = null;
                        // Content
                        let content = (input.tagName === 'INPUT' || input.tagName === 'TEXTAREA') ? input.value : input.textContent;
                        // Check if that is a valid date
                        if (Helpers.isValidDateFormat(content)) {
                            value = content;
                        } else if (self.format) {
                            let tmp = Mask.extractDateFromString(content, self.format);
                            if (tmp) {
                                value = tmp;
                            }
                        }
                        // Change the calendar view
                        if (value) {
                            setValue(value);
                        }
                    }
                }
            }
        }

        // Onload
        onload(() => {
            if (self.type !== "inline") {
                // Create modal instance
                self.modal = {
                    width: 300,
                    closed: true,
                    focus: false,
                    onopen: onopen,
                    onclose: onclose,
                    position: 'absolute',
                    'auto-close': false,
                    'auto-adjust': true,
                };
                // Generate modal
                Modal(self.el, self.modal);
            }

            let ret;

            // Create input controls
            if (self.input && self.initInput !== false) {
                if (! self.input.parentNode) {
                    self.el.parentNode.insertBefore(self.input, self.el);
                }

                let input = getInput();
                if (input && input.tagName) {
                    input.classList.add('lm-input');
                    input.classList.add('lm-calendar-input');
                    input.addEventListener('click', events.click);
                    input.addEventListener('input', events.input);
                    input.addEventListener('keydown', events.keydown);
                    input.addEventListener('focusin', events.focusin);
                    input.addEventListener('focusout', events.focusout);
                    if (self.placeholder) {
                        input.setAttribute('placeholder', self.placeholder);
                    }
                    if (self.onChange) {
                        input.addEventListener('change', self.onChange);
                    }

                    // Retrieve the value
                    if (self.value) {
                        input.value = render(self.value);
                    } else {
                        let value = extractValueFromInput();
                        if (value && value !== self.value) {
                            ret = value;
                        }
                    }
                }
            }

            // Update the internal date values
            if (ret) {
                self.setValue(ret);
            } else {
                setValue(self.value);
            }

            // Reload view
            reloadView(true);

            /**
             * Handler keyboard
             * @param {object} e - event
             */
            self.el.addEventListener('keydown', function(e) {
                let prevent = false;
                if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
                    if (e.target !== self.content) {
                        self.content.focus();
                    }
                    prev(e);
                    prevent = true;
                } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
                    if (e.target !== self.content) {
                        self.content.focus();
                    }
                    next(e);
                    prevent = true;
                } else if (e.key === 'Enter') {
                    if (e.target === self.content) {
                        // Item
                        if (self.cursor.current) {
                            // Select
                            select(e, self.cursor.current);
                            prevent = true;
                        }
                    }
                } else if (e.key === 'Escape') {
                    if (! self.isClosed()) {
                        self.close({ origin: 'escape' });
                        prevent = true;
                    }
                }

                if (prevent) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                }
            });

            /**
             * Mouse wheel handler
             * @param {object} e - mouse event
             */
            self.content.addEventListener('wheel', function(e){
                if (self.wheel !== false) {
                    if (e.deltaY < 0) {
                        prev(e);
                    } else {
                        next(e);
                    }
                    e.preventDefault();
                }
            }, { passive: false });

            /**
             * Range handler
             * @param {object} e - mouse event
             */
            self.content.addEventListener('mouseover', function(e){
                let parent = e.target.parentNode
                if (parent === self.content) {
                    let index = Array.prototype.indexOf.call(parent.children, e.target);
                    updateRange(self.options[index]);
                }
            });

            // Create event for focus out
            self.el.addEventListener("focusout", (e) => {
                let input = getInput();
                if (e.relatedTarget !== input && ! self.el.contains(e.relatedTarget)) {
                    self.close({ origin: 'focusout' });
                }
            });
        });

        onchange((prop) => {
            if (prop === 'view') {
                reloadView(true);
            } else if (prop === 'startingDay') {
                if (typeof self.startingDay !== 'number') {
                    self.startingDay = Number(self.startingDay) || 0;
                }
                self.weekdays = getWeekdays(self.startingDay);
            } else if (prop === 'value') {
                dispatchOnChangeEvent();
            }
        })

        // Tracking variables
        track('value');

        // Public methods

        self.open = function(e) {
            if (self.modal) {
                if (self.type === 'auto') {
                    self.type = window.innerWidth > 640 ? self.type = 'default' : 'picker';
                }
                self.modal.open();
            }
        }

        self.close = function(options) {
            if (self.modal) {
                if (options && options.origin) {
                    self.modal.close(options)
                } else {
                    self.modal.close({ origin: 'button' })
                }
            }
        }

        self.isClosed = function() {
            if (self.modal) {
                return self.modal.isClosed();
            }
        }

        self.getValue = function() {
            return self.value;
        }

        self.setValue = function(v) {
            // Update value
            if (v) {
                let ret = normalize(v);
                if (isTrue(self.numeric)) {
                    ret = ret.map(entry => {
                        return Helpers.dateToNum(entry);
                    })
                }

                if (! Array.isArray(v)) {
                    ret = ret.join(',');
                }

                if (ret == Number(ret)) {
                    ret = Number(ret);
                }

                v = ret;
            }

            // Events
            if (v !== self.value) {
                self.value = v;
            }
        }

        self.onevent = function(e) {
            if (events[e.type]) {
                events[e.type](e);
            }
        }

        self.update = update;
        self.next = next;
        self.prev = prev;
        self.reset = reset;
        self.setView = setView;
        self.helpers = Helpers;
        self.helpers.getDate = Mask.getDate;

        return render => render`<div class="lm-calendar" data-grid="{{self.grid}}" data-type="{{self.type}}" data-disabled="{{self.disabled}}" data-starting-day="{{self.startingDay}}">
            <div class="lm-calendar-options">
                <button type="button" onclick="${reset}">${T('Reset')}</button>
                <button type="button" onclick="${update}">${T('Done')}</button>
            </div>
            <div class="lm-calendar-container" data-view="{{self.view}}">
                <div class="lm-calendar-header">
                    <div>
                        <div class="lm-calendar-labels"><button type="button" onclick="${setView}" data-view="months">{{self.month}}</button> <button type="button" onclick="${setView}" data-view="years">{{self.year}}</button></div> 
                        <div class="lm-calendar-navigation">
                            <button type="button" class="lm-calendar-icon lm-ripple" onclick="${prev}" tabindex="0">expand_less</button>
                            <button type="button" class="lm-calendar-icon lm-ripple" onclick="${next}" tabindex="0">expand_more</button>
                        </div>
                    </div>
                    <div class="lm-calendar-weekdays" :loop="self.weekdays"><div>{{self.title}}</div></div>
                </div>
                <div class="lm-calendar-content" :loop="self.options" tabindex="0" :ref="self.content">
                    <div data-start="{{self.start}}" data-end="{{self.end}}" data-last="{{self.last}}" data-range="{{self.range}}" data-event="{{self.data}}" data-grey="{{self.grey}}" data-bold="{{self.bold}}" data-selected="{{self.selected}}" data-disabled="{{self.disabled}}" onclick="${select}">{{self.title}}</div>
                </div>
                <div class="lm-calendar-footer" data-visible="{{self.footer}}">
                    <div class="lm-calendar-time" data-visible="{{self.time}}"><select :loop="${hours}" :bind="self.hour" class="lm-calendar-control"><option value="{{self.value}}">{{self.title}}</option></select>:<select :loop="${minutes}" :bind="self.minute" class="lm-calendar-control"><option value="{{self.value}}">{{self.title}}</option></select></div>
                    <div class="lm-calendar-update"><input type="button" value="${T('Update')}" onclick="${update}" class="lm-ripple lm-input"></div>
                </div>
            </div>
        </div>`
    }

    // Register the LemonadeJS Component
    lemonade.setComponents({ Calendar: Calendar });
    // Register the web component
    lemonade.createWebComponent('calendar', Calendar);

    return function (root, options) {
        if (typeof (root) === 'object') {
            lemonade.render(Calendar, root, options)
            return options;
        } else {
            return Calendar.call(this, root)
        }
    }
})));

/***/ }),

/***/ 392:
/***/ (function(module) {

/**
 * pin the modal to the left panel
 */


;(function (global, factory) {
     true ? module.exports = factory() :
    0;
}(this, (function () {

    class CustomEvents extends Event {
        constructor(type, props, options) {
            super(type, {
                bubbles: true,
                composed: true,
                ...options,
            });

            if (props) {
                for (const key in props) {
                    // Avoid assigning if property already exists anywhere on `this`
                    if (! (key in this)) {
                        this[key] = props[key];
                    }
                }
            }
        }
    }

    // Dispatcher
    const Dispatch = function(method, type, options) {
        // Try calling the method directly if provided
        if (typeof method === 'function') {
            let a = Object.values(options);
            return method(...a);
        } else if (this.tagName) {
            this.dispatchEvent(new CustomEvents(type, options));
        }
    }

    // References
    const modals = [];
    // State of the resize and move modal
    let state = {};
    // Internal controls of the action of resize and move
    let controls = {};
    // Width of the border
    let cornerSize = 10;
    // Container with minimized modals
    const minimizedModals = [];
    // Default z-index for the modals
    const defaultZIndex = 20;

    /**
     * Send the modal to the front
     * @param container
     */
    const sendToFront = function(container) {
        let highestXIndex = defaultZIndex;
        for (let i = 0; i < modals.length; i++) {
            const zIndex = parseInt(modals[i].el.style.zIndex);
            if (zIndex > highestXIndex) {
                highestXIndex = zIndex;
            }
        }
        container.style.zIndex = highestXIndex + 1;
    }

    /**
     * Send modal to the back
     * @param container
     */
    const sendToBack = function(container) {
        container.style.zIndex = defaultZIndex;
    }

    // Get the coordinates of the action
    const getCoords = function(e) {
        let x;
        let y;

        if (e.changedTouches && e.changedTouches[0]) {
            x = e.changedTouches[0].clientX;
            y = e.changedTouches[0].clientY;
        } else {
            x = e.clientX;
            y = e.clientY;
        }

        return [x,y];
    }

    // Get the button status
    const getButton = function(e) {
        e = e || window.event;
        if (e.buttons) {
            return e.buttons;
        } else if (e.button) {
            return e.button;
        } else {
            return e.which;
        }
    }

    // Finalize any potential action
    const mouseUp = function(e) {
        // Finalize all actions
        if (typeof(controls.action) === 'function') {
            controls.action();
        }
        setTimeout(function() {
            // Remove cursor
            if (controls.e) {
                controls.e.style.cursor = '';
            }
            // Reset controls
            controls = {};
            // Reset state controls
            state = {
                x: null,
                y: null,
            }
        }, 0)
    }

    const mouseMove = function(e) {
        if (! getButton(e)) {
            return false;
        }
        // Get mouse coordinates
        let [x,y] = getCoords(e);

        // Move modal
        if (controls.type === 'move') {
            if (state && state.x == null && state.y == null) {
                state.x = x;
                state.y = y;
            }

            let dx = x - state.x;
            let dy = y - state.y;
            let top = controls.e.offsetTop + dy;
            let left = controls.e.offsetLeft + dx;

            // Update position
            controls.top = top;
            controls.left = left;
            controls.e.style.top = top + 'px';
            controls.e.style.left = left + 'px';

            state.x = x;
            state.y = y;
            state.top = top;
            state.left = left;
        } else if (controls.type === 'resize') {
            let top = null;
            let left = null;
            let width = null;
            let height = null;

            if (controls.d === 'e-resize' || controls.d === 'ne-resize' || controls.d === 'se-resize') {
                width = controls.w + (x - controls.x);

                if (e.shiftKey) {
                    height = controls.h + (x - controls.x) * (controls.h / controls.w);
                }
            } else if (controls.d === 'w-resize' || controls.d === 'nw-resize'|| controls.d === 'sw-resize') {
                left = controls.l + (x - controls.x);
                // Do not move further
                if (left >= controls.l) {
                    left = controls.l;
                }
                // Update width
                width = controls.l + controls.w - left;
                // Consider shift to update height
                if (e.shiftKey) {
                    height = controls.h - (x - controls.x) * (controls.h / controls.w);
                }
            }

            if (controls.d === 's-resize' || controls.d === 'se-resize' || controls.d === 'sw-resize') {
                if (! height) {
                    height = controls.h + (y - controls.y);
                }
            } else if (controls.d === 'n-resize' || controls.d === 'ne-resize' || controls.d === 'nw-resize') {
                top = controls.t + (y - controls.y);
                // Do not move further
                if (top >= controls.t) {
                    top = controls.t;
                }
                // Update height
                height = controls.t + controls.h - top;
            }

            if (top) {
                controls.e.style.top = top + 'px';
            }
            if (left) {
                controls.e.style.left = left + 'px';
            }
            if (width) {
                controls.e.style.width = width + 'px';
            }
            if (height) {
                controls.e.style.height = height + 'px';
            }
        }
    }

    if (typeof(document) !== "undefined") {
        document.addEventListener('mouseup', mouseUp);
        document.addEventListener('mousemove', mouseMove);
    }

    const isTrue = function(e) {
        return e === true || e === 1 || e === 'true';
    }

    const refreshMinimized = function() {
        let items = minimizedModals;
        let numOfItems = items.length;
        let width = 10;
        let height = 55;
        let offsetWidth = window.innerWidth;
        let offsetHeight = window.innerHeight;
        for (let i = 0; i < numOfItems; i++) {
            let item = items[i];
            item.el.style.left = width + 'px';
            item.el.style.top = offsetHeight - height + 'px';
            width += 205;

            if (offsetWidth - width < 205) {
                width = 10;
                height += 50;
            }
        }
    }

    const delayAction = function(self, action) {
        // Make sure to remove the transformation before minimize to preserve the animation
        if (self.el.style.marginLeft || self.el.style.marginTop) {
            // Make sure no animation during this process
            self.el.classList.add('action');
            // Remove adjustment
            removeMargin(self);
            // Make sure to continue with minimize
            setTimeout(function() {
                // Remove class
                self.el.classList.remove('action');
                // Call action
                action(self);
            },0)

            return true;
        }
    }

    const setMini = function(self) {
        if (delayAction(self, setMini)) {
            return;
        }

        // Minimize modals
        minimizedModals.push(self);

        self.el.top = self.el.offsetTop;
        self.el.left = self.el.offsetLeft;

        if (! self.el.style.top) {
            self.el.style.top = self.el.top + 'px';
        }
        if (! self.el.style.left) {
            self.el.style.left = self.el.left + 'px';
        }

        self.el.translateY = 0;
        self.el.translateX = 0;

        // Refresh positions
        setTimeout(function() {
            refreshMinimized();
            self.minimized = true;
        },10)
    }

    const removeMini = function(self) {
        minimizedModals.splice(minimizedModals.indexOf(self), 1);
        self.minimized = false;
        self.el.style.top = self.el.top + 'px';
        self.el.style.left = self.el.left + 'px';
        // Refresh positions
        setTimeout(() => {
            refreshMinimized();
        }, 10);
        // Refresh positions
        setTimeout(() => {
            if (self.top === '') {
                self.el.style.top = '';
            }
            if (self.left === '') {
                self.el.style.left = '';
            }
        }, 400);
    }

    const removeMargin = function(self) {
        if (self.el.style.marginLeft) {
            let y = self.el.offsetLeft;
            self.el.style.marginLeft = '';
            self.left = y;
        }

        if (self.el.style.marginTop) {
            let x = self.el.offsetTop;
            self.el.style.marginTop = '';
            self.top = x;
        }
    }

    const adjustHorizontal = function(self) {
        if (! isTrue(self['auto-adjust'])) {
            return false;
        }

        self.el.style.marginLeft = '';
        let viewportWidth = window.innerWidth;
        let margin = 10;

        if (self.position) {
            if (self.position === 'absolute') {
                let w = document.documentElement.offsetWidth;
                if (w > viewportWidth) {
                    //viewportWidth = w;
                }
            } else if (self.position !== 'center') {
                margin = 0;
            }
        }

        let el = self.el.getBoundingClientRect();

        let rightEdgeDistance = viewportWidth - (el.left + el.width);
        let transformX = 0;

        if (self.position === 'absolute') {
            if (rightEdgeDistance < 0) {
                transformX = rightEdgeDistance - margin - 10; // 10 is the scroll width
            }
        } else {
            if (rightEdgeDistance < 0) {
                transformX = rightEdgeDistance - margin;
            }
        }

        if (el.left < 0) {
            transformX = margin - el.left;
        }
        if (transformX !== 0) {
            self.el.style.marginLeft = transformX + 'px';
        }
    }

    const adjustVertical = function(self) {
        if (! isTrue(self['auto-adjust'])) {
            return false;
        }

        self.el.style.marginTop = '';
        let viewportHeight = window.innerHeight;
        let margin = 10;

        if (self.position) {
            if (self.position === 'absolute') {
                let h = document.documentElement.offsetHeight;
                if (h > viewportHeight) {
                    //viewportHeight = h;
                }
            } else if (self.position !== 'center') {
                margin = 0;
            }
        }

        let el = self.el.getBoundingClientRect();

        let bottomEdgeDistance = viewportHeight - (el.top + el.height);
        let transformY = 0;

        if (self.position === 'absolute') {
            if (bottomEdgeDistance < 5) {
                transformY = (-1 * el.height) - margin - 12;
                if (el.top + transformY < 0) {
                    transformY = -el.top + 10;
                }
            }
        } else {
            if (bottomEdgeDistance < 0) {
                transformY = bottomEdgeDistance - margin;
            }
        }

        if (el.top < 0) {
            transformY = margin - el.top;
        }
        if (transformY !== 0) {
            self.el.style.marginTop = transformY + 'px';
        }
    }

    const removeElements = function(root) {
        // Keep the DOM elements
        let elements = [];
        if (root) {
            while (root.firstChild) {
                elements.push(root.firstChild);
                root.firstChild.remove();
            }
        }
        return elements;
    }

    const appendElements = function(root, elements) {
        if (elements && elements.length) {
            while (elements[0]) {
                root.appendChild(elements.shift());
            }
        }
    }

    const Modal = function (template, { onchange, onload, track }) {
        let self = this;
        let backdrop = null;
        let elements = null;

        if (this.tagName) {
            // Remove elements from the DOM
            elements = removeElements(this);

            this.addEventListener('dragstart', (e) => {
                e.preventDefault();
            });
        }

        // Make sure keep the state as boolean
        self.closed = !! self.closed;

        // Keep all modals references
        modals.push(self);

        // External onload remove from the lifecycle
        let change = self.onchange;
        self.onchange = null;

        let load = self.onload;
        self.onload = null;

        let ignoreEvents = false;

        const click = function(e) {
            if (e.target.classList.contains('lm-modal-close')) {
                self.close({ origin: 'button' });
            }

            if (e.target.classList.contains('lm-modal-minimize')) {
                // Handles minimized modal positioning
                if (self.minimized === true) {
                    removeMini(self);
                } else {
                    setMini(self);
                }
            }
        }

        const mousemove = function(e) {
            if (getButton(e)) {
                return;
            }

            // Get mouse coordinates
            let [x,y] = getCoords(e);
            // Root element of the component
            let item = self.el;
            // Get the position and dimensions
            let rect = item.getBoundingClientRect();

            controls.type = null;
            controls.d = null;
            controls.e = item;
            controls.w = rect.width;
            controls.h = rect.height;
            controls.t = rect.top;
            controls.l = rect.left;

            // When resizable
            if (isTrue(self.resizable)) {
                if (e.clientY - rect.top < cornerSize) {
                    if (rect.width - (e.clientX - rect.left) < cornerSize) {
                        item.style.cursor = 'ne-resize';
                    } else if (e.clientX - rect.left < cornerSize) {
                        item.style.cursor = 'nw-resize';
                    } else {
                        item.style.cursor = 'n-resize';
                    }
                } else if (rect.height - (e.clientY - rect.top) < cornerSize) {
                    if (rect.width - (e.clientX - rect.left) < cornerSize) {
                        item.style.cursor = 'se-resize';
                    } else if (e.clientX - rect.left < cornerSize) {
                        item.style.cursor = 'sw-resize';
                    } else {
                        item.style.cursor = 's-resize';
                    }
                } else if (rect.width - (e.clientX - rect.left) < cornerSize) {
                    item.style.cursor = 'e-resize';
                } else if (e.clientX - rect.left < cornerSize) {
                    item.style.cursor = 'w-resize';
                } else {
                    item.style.cursor = '';
                }

                if (item.style.cursor) {
                    controls.type = 'resize';
                    controls.d = item.style.cursor;
                } else {
                    controls.type = null;
                    controls.d = null;
                }
            }

            if (controls.type == null && isTrue(self.draggable)) {
                if (y - rect.top < 40) {
                    item.style.cursor = 'move';
                } else {
                    item.style.cursor = '';
                }

                if (item.style.cursor) {
                    controls.type = 'move';
                    controls.d = item.style.cursor;
                } else {
                    controls.type = null;
                    controls.d = null;
                }
            }
        }

        const mousedown = function(e) {
            if (! self.minimized) {
                // Get mouse coordinates
                let [x,y] = getCoords(e);
                controls.x = x;
                controls.y = y;
                // Root element of the component
                let item = self.el;
                // Get the position and dimensions
                let rect = item.getBoundingClientRect();
                controls.e = item;
                controls.w = rect.width;
                controls.h = rect.height;
                controls.t = rect.top;
                controls.l = rect.left;
                // If is not minimized
                if (controls.type === 'resize') {
                    // Make sure the width and height is defined for the modal
                    if (! item.style.width) {
                        item.style.width = controls.w + 'px';
                    }
                    if (! item.style.height) {
                        item.style.height = controls.h + 'px';
                    }
                    // This will be the callback when finalize the resize
                    controls.action = function () {
                        self.width = parseInt(item.style.width);
                        self.height = parseInt(item.style.height);
                        controls.e.classList.remove('action');
                        // Event
                        Dispatch.call(self, self.onresize, 'resize', {
                            instance: self,
                            width: self.width,
                            height: self.height,
                        });
                    }
                    controls.e.classList.add('action');
                } else if (isTrue(self.draggable) && y - rect.top < 40) {
                    // Callback
                    controls.action = function () {
                        self.top = parseInt(item.style.top);
                        self.left = parseInt(item.style.left);
                        controls.e.classList.remove('action');
                        // Open event
                        Dispatch.call(self, self.onmove, 'move', {
                            instance: self,
                            top: self.top,
                            left: self.left,
                        });
                    }
                    controls.e.classList.add('action');
                    // Remove transform
                    removeMargin(self);
                }
            }
        }

        self.back = function() {
            sendToBack(self.el);
        }

        self.front = function() {
            sendToFront(self.el);
        }

        self.open = function() {
            if (self.closed === true) {
                self.closed = false;
                // Close event
                Dispatch.call(self, self.onopen, 'open', {
                    instance: self
                });
            }
        }

        self.close = function(options) {
            if (self.closed === false) {
                self.closed = true;
                // Close event
                Dispatch.call(self, self.onclose, 'close', {
                    instance: self,
                    ...options
                });
            }
        }

        self.isClosed = function() {
            return self.closed;
        }

        if (! template || typeof(template) !== 'string') {
            template = '';
        }

        // Custom Root Configuration
        self.settings = {
            getRoot: function() {
                return self.root;
            }
        }

        // Native lemonade
        onload(() => {
            // Dimensions
            if (self.width) {
                self.el.style.width = self.width + 'px';
            }
            if (self.height) {
                self.el.style.height = self.height + 'px';
            }
            // Position
            if (self.top) {
                self.el.style.top = self.top + 'px';
            }
            if (self.left) {
                self.el.style.left = self.left + 'px';
            }

            if (self.position === 'absolute' || self.position === 'right' || self.position === 'bottom' || self.position === 'left') {

            } else {
                if (!self.width && self.el.offsetWidth) {
                    self.width = self.el.offsetWidth;
                }
                if (!self.height && self.el.offsetHeight) {
                    self.height = self.el.offsetHeight;
                }

                // Initial centralize
                if (self.position === 'center' || !self.top) {
                    self.top = (window.innerHeight - self.height) / 2;
                }
                if (self.position === 'center' || !self.left) {
                    self.left = (window.innerWidth - self.width) / 2;
                }

                // Responsive
                if (document.documentElement.clientWidth < 800) {
                    // Full screen
                    if (self.height > 300) {
                        self.el.classList.add('fullscreen');
                    }
                }
            }

            // Auto adjust
            adjustHorizontal(self);
            adjustVertical(self);

            // Backdrop
            if (self.backdrop === true) {
                backdrop = document.createElement('div');
                backdrop.classList.add('lm-modal-backdrop');
                backdrop.addEventListener('click', () => {
                    self.close({ origin: 'backdrop' });
                });

                if (self.closed === false) {
                    self.el.parentNode.insertBefore(backdrop, self.el);
                }
            }

            // Import content from DOM
            if (self.content) {
                if (typeof(self.content) === 'string') {
                    template = self.content;
                } else if (typeof(self.content) === 'object' && self.content.tagName) {
                    self.root.appendChild(self.content);
                }
            }

            // Focus out of the component
            self.el.addEventListener('focusout', function(e) {
                if (! self.el.contains(e.relatedTarget)) {
                    if (isTrue(self['auto-close'])) {
                        self.close({ origin: 'focusout' });
                    }
                    // Remove focus
                    self.el.classList.remove('lm-modal-focus');
                }
            });

            // Focus out of the component
            self.el.addEventListener('focusin', function(e) {
                self.el.classList.add('lm-modal-focus');
            });

            // Close and stop propagation
            self.el.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    if (self.closed === false) {
                        self.close({ origin: 'escape' });
                        e.preventDefault();
                        e.stopImmediatePropagation();
                    }
                } else if (e.key === 'Enter') {
                    click(e);
                }
            });

            // Append elements to the container
            appendElements(self.el.children[1], elements);

            if (self.url) {
                fetch(self.url)
                    .then(response => response.clone().body)
                    .then(body => {
                        let reader = body.getReader();
                        reader.read().then(({ done, value }) => {
                            // Add HTML to the modal
                            self.root.innerHTML = new TextDecoder().decode(value.buffer);
                            // Call onload event
                            Dispatch.call(self, load, 'load', {
                                instance: self
                            });
                        });
                    });
            } else {
                // Call onload event
                Dispatch.call(self, load, 'load', {
                    instance: self
                });
            }
        });

        onchange((property) => {
            if (ignoreEvents) {
                return false;
            }

            if (property === 'closed') {
                if (self.closed === false) {
                    // Focus on the modal
                    if (self.focus !== false) {
                        self.el.focus();
                    }
                    // Show backdrop
                    if (backdrop) {
                        self.el.parentNode.insertBefore(backdrop, self.el);
                    }

                    // Auto adjust
                    queueMicrotask(() => {
                        adjustHorizontal(self);
                        adjustVertical(self);
                    });
                } else {
                    // Hide backdrop
                    if (backdrop) {
                        backdrop.remove();
                    }
                }
            } else if (property === 'top' || property === 'left' || property === 'width' || property === 'height') {
                if (self[property] !== '') {
                    self.el.style[property] = self[property] + 'px';
                } else {
                    self.el.style[property] = '';
                }

                if (self.closed === false) {
                    queueMicrotask(() => {
                        if (property === 'top') {
                            adjustVertical(self);
                        }
                        if (property === 'left') {
                            adjustHorizontal(self);
                        }
                    });
                }
            } else if (property === 'position') {
                if (self.position) {
                    if (self.position === 'center') {
                        self.top = (window.innerHeight - self.el.offsetHeight) / 2;
                        self.left = (window.innerWidth - self.el.offsetWidth) / 2;
                    } else {
                        self.top = '';
                        self.left = '';
                    }
                } else {
                    if (! self.top) {
                        self.top = (window.innerHeight - self.el.offsetHeight) / 2;
                    }
                    if (! self.left) {
                        self.left = (window.innerWidth - self.el.offsetWidth) / 2;
                    }
                }
            }
        });

        track('top');
        track('left');
        track('width');
        track('height');

        return render => render`<div class="lm-modal" animation="{{self.animation}}" position="{{self.position}}" closed="{{self.closed}}" closable="{{self.closable}}" minimizable="{{self.minimizable}}" minimized="{{self.minimized}}" overflow="{{self.overflow}}" tabindex="-1" role="modal" onmousedown="${mousedown}" onmousemove="${mousemove}" onclick="${click}">
            <div class="lm-modal-title" data-title="{{self.title}}" data-icon="{{self.icon}}"><div class="lm-modal-icon">{{self.icon}}</div><div>{{self.title}}</div><div class="lm-modal-icon lm-modal-minimize" tabindex="0"></div><div class="lm-modal-icon lm-modal-close" tabindex="0"></div></div>
            <div :ref="self.root">${template}</div>
        </div>`
    }

    const Component = function (root, options) {
        if (typeof(root) === 'object') {
            // Remove elements from the DOM
            let elements = removeElements(root);
            // Create the modal
            let e = lemonade.render(Modal, root, options);
            // Add elements to the container
            appendElements(e.children[1], elements);

            return options;
        } else {
            return Modal.call(this);
        }
    }

    // Create LemonadeJS Component
    lemonade.setComponents({ Modal: Modal });
    // Create Web Component
    lemonade.createWebComponent('modal', Modal)

    return Component;
})));

/***/ }),

/***/ 256:
/***/ (function(module, __unused_webpack_exports, __webpack_require__) {

const lemonade = __webpack_require__(926);

;(function (global, factory) {
     true ? module.exports = factory() :
    0;
}(this, (function () {

    function padZero(i) {
        return i < 10 ? '0' + i : i;
    }

    // Convert time string (HH:MM) to minutes since midnight
    function timeToMinutes(timeStr) {
        if (!timeStr) return 0;
        const parts = timeStr.split(':');
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }

    // Initialize all possible time values
    const allTimeValues = [];

    // Loop through each hour of the day
    for (let hour = 0; hour < 24; hour++) {
        // Loop through each 5 minute interval in an hour
        for (let minute = 0; minute < 60; minute += 5) {
            // Format the time string
            const time = `${padZero(hour)}:${padZero(minute)}`;
            // Add the formatted time to the array
            allTimeValues.push({
                text: time,
                value: time
            });
        }
    }

    // Get available time values based on validRange
    const getAvailableTimeValues = function(range) {
        let filteredValues = allTimeValues;

        // Filter by validRange if provided (only show times within this range)
        if (range && range.length === 2) {
            const startMinutes = timeToMinutes(range[0]);
            const endMinutes = timeToMinutes(range[1]);

            filteredValues = filteredValues.filter(function(item) {
                const itemMinutes = timeToMinutes(item.value);
                return itemMinutes >= startMinutes && itemMinutes <= endMinutes;
            });
        }

        return filteredValues;
    }

    const Event = function(children, { setPath, onchange }) {
        let self = this;
        let registerCallback = null;

        let [ data, setData ] = setPath({});

        // Initialize timeValues
        let validRange = getAvailableTimeValues(self.validRange);

        self.palette = [
            [ "#f44336", "#e91e63", "#9c27b0", "#3f51b5" ],
            [ "#2196f3", "#00bcd4", "#009688", "#4caf50" ],
            [ "#8bc34a", "#cddc39", "#ffeb3b", "#ffc107" ],
            [ "#ff9800", "#ff5722", "#795548", "#9e9e9e" ]
        ];

        self.open = function(record, callback) {
            // Open the modal
            self.modal.open();
            // Load data
            setData(record);
            // Register save
            registerCallback = callback;
        }

        const save = () => {
            registerCallback(data);
            // Close the modal
            self.modal.close();
        }

        onchange((prop) => {
            if (prop === 'validRange') {
                validRange = getAvailableTimeValues(self.validRange);
            }
        })

        return render => render`<div>
            <lm-modal title="Event information" :ref="self.modal" :closable="true" :draggable="true" :width="400" :height="380" :closed="true" icon="edit_calendar">
                <form :ref="self.form" data-readonly="{{self.readonly}}" class="lm-p20">
                    <div class="lm-form-group">
                        <input type="text" placeholder="Title" :path="title" />
                    </div>
                    <div class="lm-form-group lm-row">
                        <div class="lm-column lm-f1" style="margin-right: 8px;">
                            <Calendar input="auto" :footer="false" placeholder="When" :path="date" format="dd/mm/yyyy" />
                        </div><div class="lm-column" style="margin-right: 8px;">
                            <Dropdown :data="${validRange}" width="80" :path="start" />
                        </div><div class="lm-column">
                            <Dropdown :data="${validRange}" width="80" :path="end" />
                        </div>
                    </div>
                    <div class="lm-form-group">
                        <input type="text" placeholder="Location" :path="location" />
                    </div>
                    <div class="lm-form-group">
                        <Color input="auto" placeholder="Color" :palette="self.palette" :path="color" :closeOnChange="true"  />
                    </div>
                    <div class="lm-form-group">
                        <input type="button" class="lm-button lm-w100" value="Save" onclick="${save}">
                    </div>
                </form>
            </lm-modal>
        </div>`;
    }

    lemonade.setComponents({ Event: Event });

    // Register the web component
    lemonade.createWebComponent('lm-event', Event);

    return function (root, options) {
        if (typeof (root) === 'object') {
            lemonade.render(Event, root, options)
            return options;
        } else {
            return Event.call(this, root)
        }
    }
})));


/***/ }),

/***/ 108:
/***/ (function(module) {



const History = (function(changes) {
    /**
     * Add entry in the history
     */
    const component = function(changes) {
        if (this.ignoreHistory !== true) {
            // Increment and get the current history index
            let index = ++this.historyIndex;
            // Slice the array to discard undone changes
            this.history = (this.history = this.history.slice(0, index + 1));
            // Keep history
            this.history[index] = changes;
        }
    }

    component.undo = function() {
        let historyRecord = null;

        // Update cells
        if (this.historyIndex >= 0) {
            // History
            historyRecord = this.history[this.historyIndex--];
        }

        if (historyRecord) {
            // Ignore
            this.ignoreHistory = true;
            // Records
            if (historyRecord.action === 'addEvents') {
                this.deleteEvents(historyRecord.records);
            } else if (historyRecord.action === 'deleteEvents') {
                this.addEvents(historyRecord.records);
            } else if (historyRecord.action === 'updateEvent') {
                this.updateEvent(historyRecord.guid, historyRecord.oldValue);
            } else if (historyRecord.action === 'setData') {
                this.setData(historyRecord.oldData);
            }

            if (typeof (this.onchange) == 'function') {
                this.onchange(this);
            }

            // Back to track
            this.ignoreHistory = false;
        }
    }

    component.redo = function() {
        let historyRecord = null;

        // Update cells
        if (this.historyIndex < this.history.length - 1) {
            // History
            historyRecord = this.history[++this.historyIndex];
        }

        if (historyRecord) {
            // Ignore
            this.ignoreHistory = true;
            // Records
            if (historyRecord.action === 'addEvents') {
                this.addEvents(historyRecord.records);
            } else if (historyRecord.action === 'deleteEvents') {
                this.deleteEvents(historyRecord.records);
            } else if (historyRecord.action === 'updateEvent') {
                this.updateEvent(historyRecord.guid, historyRecord.newValue);
            } else if (historyRecord.action === 'setData') {
                this.setData(historyRecord.newData);
            }

            if (typeof (this.onchange) == 'function') {
                this.onchange(this);
            }

            // Back tracking
            this.ignoreHistory = false;
        }
    }

    component.reset = function() {
        // Slice the array to discard undone changes
        this.historyIndex = -1;
        // Keep history
        this.history = [];
        // Control flag
        this.ignoreHistory = false;
    }

    return component;
})();

/**
 * Todo:
 * Ctrl+arrow para mover event po sition
 * Shift+arrow to change size of event
 * Selection all event
 * Move multiple events
 */
;(function (global, factory) {
     true ? module.exports = factory() :
    0;
}(this, (function () {

    const guid = function() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    const Two = function(value) {
        value = '' + value;
        if (value.length == 1) {
            value = '0' + value;
        }
        return value;
    }

    const Translate = function(t) {
        if (typeof(document) !== "undefined" && document.dictionary) {
            return document.dictionary[t] || t;
        } else {
            return t;
        }
    }

    const dateToArray = function (value) {
        let date = value.split(((value.indexOf('T') !== -1) ? 'T' : ' '));
        let time = date[1];
        date = date[0].split('-');
        let y = parseInt(date[0]);
        let m = parseInt(date[1]);
        let d = parseInt(date[2]);
        let h = 0;
        let i = 0;

        if (time) {
            time = time.split(':');
            h = parseInt(time[0]);
            i = parseInt(time[1]);
        }
        return [y, m, d, h, i, 0];
    }

    const dateToISO = function(d) {
        return new Date(d).toISOString().substring(0,10);
    }

    const Weekdays = [
        Translate('Sun'),
        Translate('Mon'),
        Translate('Tue'),
        Translate('Wed'),
        Translate('Thu'),
        Translate('Fri'),
        Translate('Sat'),
    ];

    const isLight = function(color) {
        let r,g,b;

        if (color.match(/^rgb/)) {
            color = color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+(?:\.\d+)?))?\)$/);
            r = color[1];
            g = color[2];
            b = color[3];
        } else {
            color = color.replace('#', '');
            color = +("0x" + color.slice(1).replace(color.length < 5 && /./g, '$&$&'));
            r = color >> 16;
            g = color >> 8 & 255;
            b = color & 255;
        }

        // Using the HSP value, determine whether the color is light or dark
        return Math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b)) > 160;
    }

    const Schedule = function(children, { onload, onchange, track }) {
        let self = this;

        if (! self.type) {
            self.type = 'week';
        }

        if (! Array.isArray(self.data)) {
            self.data = [];
        }

        if (! Array.isArray(self.validRange)) {
            self.validRange = [];
        }

        if (! Array.isArray(self.readOnlyRange)) {
            self.readOnlyRange = [];
        }

        self.weekly = !! self.weekly;

        // Set defaults and validate
        if (! self.grid || self.grid <= 0) {
            self.grid = 15;
        }

        if (! self.snap || self.snap <= 0) {
            self.snap = self.grid;
        }

        if (typeof self.overlap === 'undefined') {
            self.overlap = false;
        }

        // History
        History.reset.call(self);

        // Grid
        let minutesPerDivision = self.grid || 15;
        let totalDivisionByHour = 60 / minutesPerDivision;
        let totalDivisionsByDay = totalDivisionByHour * 24;
        let pasteHistory = [];
        let board = [];
        let selected = [];
        let state = null;
        let pointer = null;

        // Number of grid divisions per snap step (>= 1). Read dynamically so
        // late changes to `self.snap` take effect on the next gesture.
        const getSnapDivisions = function() {
            let snap = self.snap;
            if (! snap || snap < minutesPerDivision) {
                return 1;
            }
            return Math.max(1, Math.round(snap / minutesPerDivision));
        }

        // Snap a target row index so the resulting event size is a multiple of
        // the snap step, anchored at `state.y1`. Returns a clamped inclusive
        // end-row index.
        const snapResizeY = function(y) {
            let snapDiv = getSnapDivisions();
            if (snapDiv <= 1) {
                return y;
            }
            let anchor = state.y1;
            let snappedY;
            if (y >= anchor) {
                let rawSize = y - anchor + 1;
                let snappedSize = Math.max(snapDiv, Math.round(rawSize / snapDiv) * snapDiv);
                snappedY = anchor + snappedSize - 1;
            } else {
                let rawSize = anchor - y + 1;
                let snappedSize = Math.max(snapDiv, Math.round(rawSize / snapDiv) * snapDiv);
                snappedY = anchor - snappedSize + 1;
            }
            return Math.max(0, Math.min(totalDivisionsByDay - 1, snappedY));
        }

        const findElement = function(elements) {
            for (let i = 0; i < elements.length; i++) {
                if (elements[i].tagName === 'TD' && elements[i].getAttribute('data-x')) {
                    if (! elements[i].classList.contains('lm-schedule-disabled')) {
                        return elements[i];
                    }
                }
            }
            return false;
        }

        const setPointer = function() {
            let d = new Date();
            let hour = hourToInt(Two(d.getHours()) + ':' + Two(d.getMinutes()));
            let date = Two(d.getFullYear()) + '-' + Two(d.getMonth()+1) + '-' + Two(d.getDate());
            let column = self.el.querySelector('[data-date="'+date+'"]');
            if (column) {
                let reference = self.el.querySelector('[data-y="' + hour + '"]');
                if (reference && reference.offsetWidth) {
                    self.pointer.style.top = reference.offsetTop + 'px';
                    self.pointer.style.left = column.offsetLeft + 'px';
                    self.pointer.style.width = column.offsetWidth + 'px';
                    self.pointer.style.display = 'block';
                }
            }
        }

        const EventElement = function(children, { onload }) {
            const self = this;

            const updateColor = () => {
                if (self.color) {
                    self.el.style.setProperty("--lm-schedule-background", self.color);
                    if (isLight(self.color)) {
                        self.el.style.setProperty("--lm-schedule-color", 'black');
                    } else {
                        self.el.style.setProperty("--lm-schedule-color", 'white');
                    }
                }
            }

            const updateHeight = () => {
                self.el.style.height = (hourToInt(self.end) - hourToInt(self.start)) * minutesPerDivision + 'px';
            }

            const updateReadonly = () => {
                if (self.readonly) {
                    self.el.classList.add('readonly');
                } else {
                    self.el.classList.remove('readonly');
                }
            }

            // Define the background color
            onload(() => {
                updateColor();
                updateHeight();
                updateReadonly();
            });

            onchange((prop) => {
                if (prop === 'color') {
                    updateColor();
                } else if (prop === 'start' || prop === 'end') {
                    updateHeight();
                } else if (prop === 'readonly') {
                    updateReadonly();
                }
            })

            return render => render`<div class="lm-schedule-item" id="{{this.guid}}" data-visible="{{self.visible}}" data-warning="{{self.warning}}" data-color="{{self.color}}" data-readonly="{{self.readonly}}" data-title="{{self.title}}" data-description="{{self.description}}" data-start="{{self.start}}" data-end="{{self.end}}" data-height="{{end-start}}"></div>`;
        }

        const createEventElement = function(record, target) {
            if (! (record && record.guid)) {
                console.error('You cannot create a DOM for an event without the guid');
                return false;
            }

            let root = lemonade.render(EventElement, target, record)
            root.event = record;
            return root;
        }

        const updateEventElement = function(newRecord) {
            let element = getDomByGuid(newRecord);
            let container;
            let y = hourToInt(newRecord.start);

            // Column identification
            if (self.weekly) {
                container = document.querySelector('[data-y="'+y+'"][data-x="'+newRecord.weekday+'"]');
            } else {
                container = document.querySelector('[data-y="'+y+'"][data-date="'+newRecord.date.substring(0, 10)+'"]');
            }

            // Append element
            if (container) {
                container.appendChild(element);
            } else {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }
        }

        const createEmptyEventObject = function(v) {
            let record = {
                type: null,
                title: 'No title',
                start: '',
                end: '',
                guests: '',
                location: '',
                description: '',
                color: '#3f51b5',
                readonly: false,
                guid: guid(),
            }

            if (self.weekly) {
                record.weekday = parseInt(v) || 0;
            } else {
                record.date = v || '';
            }

            return record;
        }

        // Schema for default-filling batched events without leaking a shared guid
        const getEventSchema = function() {
            let schema = createEmptyEventObject();
            delete schema.guid;
            return schema;
        }

        const getDuration = function(e) {
            let i = e.getAttribute('data-start');
            let f = e.getAttribute('data-end');
            i = hourToInt(i);
            f = hourToInt(f);
            return f - i;
        }

        // Update label event
        const updateLabel = function(s) {
            let y1 = s.y1;
            let y2 = s.y2;
            let start;
            let end;
            let h;

            if (y1 > y2) {
                start = intToHour(y2);
                end = intToHour(y1+1);
                h = (y1-y2)+1;
            } else {
                start = intToHour(y1);
                end = intToHour(y2+1);
                h = (y2-y1)+1;
            }

            let x = s.element.parentNode.getAttribute('data-x');
            let d = s.element.parentNode.getAttribute('data-date');

            // Update label
            s.element.setAttribute('data-x', x);
            s.element.setAttribute('data-height', h);

            if (self.weekly) {
                s.element.weekday = parseInt(x);
            } else {
                s.element.date = d;
            }
            s.element.start = start;
            s.element.end = end;
            // Update DOM attributes directly so CSS ::after content refreshes during drag
            s.element.setAttribute('data-start', start);
            s.element.setAttribute('data-end', end);
        }

        const deleteEvent = function(guid) {
            let index = self.data.findIndex((evt) => evt.guid === guid);
            if (index >= 0) {
                if (self.data[index].readonly) {
                    console.error('Event is readonly');
                } else {
                    // Delete reference from data
                    let item = self.data.splice(index, 1)[0];
                    // Remove DOM element
                    let dom = getDomByGuid(item);
                    if (dom && dom.parentNode) {
                        dom.parentNode.removeChild(dom);
                    }
                    // Call event
                    if (typeof(self.ondelete) == 'function') {
                        self.ondelete(self, item);
                    }
                    return item;
                }
            }
            return null;
        }

        const getDomByGuid = function(record, root) {
            if (record.el) {
                return record.el;
            } else {
                let dom = document.getElementById(record.guid);
                if (! dom) {
                    dom = createEventElement(record, root);
                }
                return dom;
            }
        }

        // Convert int to hour
        const intToHour = function(y) {
            return Two(parseInt(y / totalDivisionByHour)) + ':' + Two((y % totalDivisionByHour) * minutesPerDivision);
        }

        // Convert hour to int
        const hourToInt = function(time) {
            if (time) {
                time = time.split(':')
                return (time[0] * totalDivisionByHour) + parseInt(time[1] / minutesPerDivision);
            }
        }

        // Is a valid DOM event
        const isEvent = function(element) {
            return element.tagName === 'DIV' && element.classList.contains('lm-schedule-item');
        }

        const isToday = function(val) {
            let today = new Date();

            if (! self.weekly) {
                if (today.getFullYear() === val.getFullYear() &&
                    today.getMonth() === val.getMonth() &&
                    today.getDate() === val.getDate()) {
                    return true;
                }
            } else {
                if (today.getDay() === val) {
                    return true;
                }
            }

            return false;
        }

        const createUTCDate = function(year, month, day) {
            // Create a date object using the local time zone.
            let date = new Date(year, month, day, 0, 0, 0);
            // Adjust for the timezone offset to get GMT/UTC time.
            date = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
            return date;
        }

        const getColumns = function() {
            let date = dateToArray(self.value);
            // Columns
            let column = [null,null,null,null,null,null,null];
            // Get the monday
            let D = createUTCDate(date[0], date[1] - 1, date[2]);

            if (! self.weekly) {
                // Adjust to start on sunday
                if (self.type === 'week' || self.type === 'weekdays') {
                    let day = D.getDay();
                    if (self.type === 'week') {
                        if (day > 0) {
                            D.setHours(-24 * day);
                        }
                    } else if (self.type === 'weekdays') {
                        D.setHours(-24 * (day - 1));
                    }
                }
                let y = D.getFullYear();
                let m = D.getMonth();
                let d = D.getDate();

                if (self.type === 'week') {
                    for (let i = 0; i < 7; i++) {
                        column[i] = createUTCDate(y, m, d + i);
                    }
                } else if (self.type === 'weekdays') {
                    for (let i = 1; i < 6; i++) {
                        column[i] = createUTCDate(y, m, d + i - 1);
                    }
                } else {
                    let i = D.getDay();
                    column[i] = createUTCDate(y, m, d);
                }
            } else {
                if (self.type === 'week') {
                    for (let i = 0; i < 7; i++) {
                        column[i] = i;
                    }
                } else if (self.type === 'weekdays') {
                    for (let i = 1; i < 6; i++) {
                        column[i] = i;
                    }
                } else {
                    let i = D.getDay();
                    column[i] = i;
                }
            }

            return column;
        }

        const renderOverlap = function() {
            // Adjust padding
            if (self.overlap === true) {
                let count = null;
                let columns = getColumns();
                let domColumnIndex = 1; // Start at 1 because children[0] is the time label column

                columns.forEach(function(column, i) {
                    if (column === null) {
                        return false;
                    }
                    let size = 0;
                    for (let j = 0; j < totalDivisionsByDay; j++) {
                        let element = self.tbody.children[j].children[domColumnIndex];
                        if (element && element.children.length) {
                            for (let y = 0; y < element.children.length; y++) {
                                let e = element.children[y];
                                let info = e.parentNode.getBoundingClientRect();
                                e.style.width = info.width - (10 * size) + 'px';
                                e.style.marginLeft = (10 * size) + 'px';
                                // Z-index
                                size++;
                                // Duration
                                info = getDuration(e);
                                if (info > count) {
                                    count = info;
                                }
                            }
                        }

                        // Events
                        if (count > 0) {
                            count--;
                            if (! count) {
                                size = 0;
                            }
                        }
                    }
                    domColumnIndex++; // Increment for the next visible column
                })
            }
        }

        const renderElements = function() {
            let columns = getColumns();
            let domColumnIndex = 1; // Start at 1 because children[0] is the time label column
            // Add new events to each visible column
            columns.forEach(function(column, x) {
                if (column === null) {
                    return false;
                }
                let value = x;
                if (! self.weekly) {
                    value = dateToISO(column);
                }
                let events = getEvents(value);
                if (events) {
                    for (let j = 0; j < events.length; j++) {

                        // Get the parent row
                        let t = hourToInt(events[j].start);
                        // Safety check: skip if row doesn't exist
                        if (t >= 0 && self.tbody.children[t] && self.tbody.children[t].children[domColumnIndex]) {
                            // Get the parent DOM element
                            let element = self.tbody.children[t].children[domColumnIndex];
                            // Get DOM element
                            let e = getDomByGuid(events[j], element);
                            if (e) {
                                element.appendChild(e);
                            }
                        }
                    }
                }
                domColumnIndex++; // Increment for the next visible column
            });

            renderOverlap();
        }

        const getHeaders = function() {
            // Get columns
            let columns = getColumns();
            let headers = [{}];

            // Create headers
            columns.forEach(function(column, day) {
                if (column === null) {
                    return false;
                }

                let record = {
                    day: day,
                    weekday: Weekdays[day],
                    value: '',
                };

                if (! self.weekly) {
                    record.value = Two(new Date(column).getDate());

                    if (isToday(column)) {
                        record.selected = true;
                    }
                } else {
                    if (new Date().getDay() === day) {
                        record.selected = true;
                    }
                }

                headers.push(record);
            })

            self.headers = headers;
        }

        // Render the table
        const getContent = function() {
            let tr = document.createElement('tr');
            let td = document.createElement('td');
            tr.appendChild(td);

            // Reset pointer
            pointer = null;

            // Create the grid
            self.tbody.textContent = '';

            let columns = getColumns();

            // Create the rows
            for (let j = 0; j < totalDivisionsByDay; j++) {
                tr = document.createElement('tr');
                tr.style.height = minutesPerDivision + 'px';
                td = document.createElement('td');
                if (! (j % totalDivisionByHour)) {
                    if (j < totalDivisionsByDay) {
                        let div = document.createElement('div');
                        div.classList.add('lm-schedule-index');
                        div.innerText = Two(j / totalDivisionByHour) + ':00'
                        td.appendChild(div);
                    }

                    // Hour line
                    tr.classList.add('lm-schedule-hour');
                }

                // Hide hours outside valid range
                if (self.validRange && self.validRange.length === 2) {
                    let r1 = hourToInt(self.validRange[0]) || 0;
                    let r2 = hourToInt(self.validRange[1]) || totalDivisionsByDay;

                    if (! (j >= r1 && j < r2)) {
                        tr.style.display = 'none';
                    }
                }

                // Check if this row should be disabled (for read-only hours)
                let isRowDisabled = false;
                if (self.readOnlyRange && self.readOnlyRange.length > 0) {
                    // Check if it's a single range ['08:00', '18:00'] or multiple ranges [['00:00', '08:00'], ['18:00', '23:59']]
                    let ranges = Array.isArray(self.readOnlyRange[0]) ? self.readOnlyRange : [self.readOnlyRange];

                    for (let k = 0; k < ranges.length; k++) {
                        if (ranges[k].length === 2) {
                            let r1 = hourToInt(ranges[k][0]) || 0;
                            let r2 = hourToInt(ranges[k][1]) || totalDivisionsByDay;

                            if (j >= r1 && j < r2) {
                                isRowDisabled = true;
                                break;
                            }
                        }
                    }
                }

                // Append to the DOM
                tr.appendChild(td);
                self.tbody.appendChild(tr);

                // Content
                columns.forEach(function(column, x) {
                    if (column === null) {
                        return false;
                    }

                    // Element
                    td = document.createElement('td');
                    td.setAttribute('data-x', x);
                    td.setAttribute('data-y', j);

                    // Apply disabled class only to time slot cells, not the hour label
                    if (isRowDisabled) {
                        td.classList.add('lm-schedule-disabled');
                    }

                    tr.appendChild(td);

                    if (! self.weekly) {
                        let date = dateToISO(column);
                        td.setAttribute('data-date', date);
                    }
                });
            }

            renderElements();
        }

        const render = function() {
            getHeaders();
            getContent();
            setPointer();
        }

        const sortEvents = function() {
            self.data = self.data.sort(function(a, b) {
                // Compare by date or weekday first
                if (self.weekly) {
                    // In weekly mode, sort by weekday
                    if (a.weekday < b.weekday) return -1;
                    if (a.weekday > b.weekday) return 1;
                } else {
                    // In normal mode, sort by date
                    if (a.date < b.date) return -1;
                    if (a.date > b.date) return 1;
                }

                // If dates/weekdays are equal, then compare by start time
                const aStartMinutes = parseInt(a.start.substr(0, 2)) * 60 + parseInt(a.start.substr(3));
                const bStartMinutes = parseInt(b.start.substr(0, 2)) * 60 + parseInt(b.start.substr(3));
                return aStartMinutes - bStartMinutes;
            })
        }

        const changeLeftEventFocus = function() {
            if (selected.length === 1) {
                let sorted = self.data;
                let prev = sorted[sorted.indexOf(selected[0]) - 1];
                if (prev) {
                    let dom = getDomByGuid(selected[0]);

                    dom.classList.remove('lm-schedule-selected');
                    selected.shift();
                    selected.push(prev);

                    dom = getDomByGuid(selected[0]);
                    dom.classList.add('lm-schedule-selected');
                }
            }
        }

        const changeRightEventFocus = function() {
            if (selected.length === 1) {
                let sorted = self.data;
                let next = sorted[sorted.indexOf(selected[0]) + 1];
                if (next) {
                    let dom = getDomByGuid(selected[0]);

                    dom.classList.remove('lm-schedule-selected');
                    selected.shift();
                    selected.push(next);

                    dom = getDomByGuid(selected[0]);
                    dom.classList.add('lm-schedule-selected');
                }
            }
        }

        const updateSelection = function(e, reset) {
            if (reset === true) {
                resetSelection();
            }
            e.classList.add('lm-schedule-selected');
            // Select event
            if (selected.indexOf(e.event) < 0) {
                selected.push(e.event);
            }
        }

        const resetSelection = function() {
            if (selected.length) {
                for (let i = 0; i < selected.length; i++) {
                    let dom = getDomByGuid(selected[i]);
                    if (dom) {
                        dom.classList.remove('lm-schedule-selected');
                    }
                }
                selected.length = 0;
            }
        }

        const getEvents = function(value) {
            let filter;

            if (self.weekly) {
                filter = function(v) {
                    if (v.weekday === value) {
                        return v;
                    }
                    return false;
                }
            } else {
                filter = function(v) {
                    if (v.date.substring(0, 10) === value) {
                        return v;
                    }
                    return false;
                }
            }

            return self.data.filter(filter);
        }

        const normalizeEvents = function(events, defaultDate) {
            let schema = getEventSchema();

            for (let i = 0; i < events.length; i ++) {
                if (!events[i] || typeof events[i] !== 'object') {
                    continue;
                }
                // Make sure all events has the necessary properties
                for (let prop in schema) {
                    if (typeof(events[i][prop]) === 'undefined') {
                        events[i][prop] = schema[prop];
                    }
                }
                // Default for start
                if (! events[i].start) {
                    events[i].start = '00:00';
                }

                // Validate start time format
                let startInt = hourToInt(events[i].start);
                if (typeof startInt === 'undefined' || isNaN(startInt)) {
                    events[i].start = '00:00';
                    startInt = 0;
                }

                // Default for end (if not provided, set to 1 hour after start)
                if (! events[i].end) {
                    events[i].end = intToHour(startInt + totalDivisionByHour);
                } else {
                    // Validate end time format
                    let endInt = hourToInt(events[i].end);
                    if (typeof endInt === 'undefined' || isNaN(endInt)) {
                        events[i].end = intToHour(startInt + totalDivisionByHour);
                    }
                }

                // Default for the date
                if (self.weekly) {
                    if (typeof events[i].weekday === 'undefined') {
                        events[i].weekday = 0;
                    }
                } else {
                    if (! events[i].date && defaultDate) {
                        events[i].date = defaultDate;
                    }
                }

                // Guid
                if (! events[i].guid) {
                    events[i].guid = guid();
                }
            }

            return events;
        }

        self.addEvents = function(events, e) {
            let date = dateToArray(self.value);

            if (! Array.isArray(events)) {
                if (events === null || typeof events != 'object') {
                    return false;
                }
                events = [events];
            }

            // Drop any non-object entries (null, undefined, scalars)
            events = events.filter(function(v) {
                return v !== null && typeof v === 'object';
            });

            if (events.length === 0) {
                return false;
            }

            // Normalize events
            normalizeEvents(events, date.join(''));

            if (self.onbeforecreate) {
                let ret = self.onbeforecreate(self, events, e);
                if (ret === false) {
                    return false;
                }
            }

            // Add event to the data list
            self.data.push(...events);

            // Sorting events
            sortEvents();

            // Need to render again
            renderElements();

            History.call(self, {
                action: 'addEvents',
                records: events
            });

            if (self.oncreate) {
                self.oncreate(self, events, e);
            }

            if (e && self.onedition) {
                self.onedition(self, events[0]);
            }

            if (e && self.onchange) {
                self.onchange(self);
            }

            return events;
        }

        self.updateEvent = function(mixed, newValue) {
            if (typeof(newValue) !== 'object') {
                return false;
            }
            let oldValue = {};
            let record = null;

            if (typeof (mixed) === 'object') {
                record = mixed;
            } else {
                let index = self.data.findIndex((evt) => evt.guid === mixed);
                if (index >= 0) {
                    record = self.data[index];
                }
            }

            let acceptedProperties = [ 'title', 'color', 'date', 'weekday', 'start', 'end', 'location' ];
            if (record) {
                // Check if event would be in disabled range
                if (newValue.start || newValue.end) {
                    let start = newValue.start !== undefined ? newValue.start : record.start;
                    let end = newValue.end !== undefined ? newValue.end : record.end;
                    let y1 = hourToInt(start);
                    let y2 = hourToInt(end);

                    if (isInDisabledRange(y1, y2)) {
                        if (typeof(self.onerror) === 'function') {
                            self.onerror(self, "Cannot place event in disabled time range");
                        }
                        return false;
                    }
                }

                // Check for overlap conflicts before applying changes
                if (!self.overlap && (newValue.start || newValue.end || newValue.date || newValue.weekday)) {
                    if (hasEventConflict(record, newValue)) {
                        if (typeof(self.onerror) === 'function') {
                            self.onerror(self, "Time conflict: This event overlaps with another event");
                        }
                        return false;
                    }
                }

                if (typeof (self.onbeforechange) === 'function') {
                    let ret = self.onbeforechange(self, { action: 'updateEvent', record: record, newValue: newValue });
                    if (ret === false) {
                        return false;
                    }
                }

                acceptedProperties.forEach(function(v) {
                    if (newValue[v] !== undefined) {
                        oldValue[v] = record[v];
                        record[v] = newValue[v];
                    }
                });

                // If the values are different from the original
                if (JSON.stringify(newValue) !== JSON.stringify(oldValue)) {
                    // Update label
                    updateEventElement(record);
                    // Sorting events
                    sortEvents();
                    // Re-render
                    renderElements();

                    History.call(self, {
                        action: 'updateEvent',
                        guid: record.guid,
                        newValue: newValue,
                        oldValue: oldValue,
                    });

                    // Send update message
                    if (typeof (self.onchangeevent) == 'function') {
                        self.onchangeevent(self, record, oldValue, newValue);
                    }

                    if (typeof (self.onchange) == 'function') {
                        self.onchange(self);
                    }
                }
            }
        }

        self.deleteEvents = function(events) {
            if (! Array.isArray(events)) {
                // Single item (object event or string guid) - convert to array
                events = [events];
            }

            if (typeof (self.onbeforechange) === 'function') {
                let ret = self.onbeforechange(self, { action: 'deleteEvents', events: events });
                if (ret === false) {
                    return false;
                }
            }

            // Remove all events
            let records = [];
            events.forEach((event) => {
                if (typeof(event) === 'object') {
                    records.push(deleteEvent(event.guid));
                } else {
                    records.push(deleteEvent(event));
                }
            });

            // Sorting events
            sortEvents();

            History.call(self, {
                action: 'deleteEvents',
                records: records
            });

            if (typeof (self.onchange) == 'function') {
                self.onchange(self);
            }
        }

        self.resetSelection = function(e) {
            // Add to the selected events
            if (e && ! e.ctrlKey || typeof(e) === 'undefined') {
                resetSelection();
            }
        }

        self.setRange = function(range) {
            if (range[0] && range[1]) {
                if (hourToInt(range[0]) && hourToInt(range[1])) {
                    self.validRange = range;

                    render();
                } else {
                    if (typeof(self.onerror) === 'function') {
                        self.onerror(self, "Invalid range time");
                    }
                }
            }
        }

        self.setReadOnly = function(range) {
            // Support single range ['08:00', '18:00'] or multiple ranges [['00:00', '08:00'], ['18:00', '23:59']]
            let ranges = Array.isArray(range[0]) ? range : [range];
            let valid = true;

            for (let i = 0; i < ranges.length; i++) {
                if (!ranges[i][0] || !ranges[i][1] || !hourToInt(ranges[i][0]) && hourToInt(ranges[i][0]) !== 0 || !hourToInt(ranges[i][1]) && hourToInt(ranges[i][1]) !== 0) {
                    valid = false;
                    break;
                }
            }

            if (valid) {
                self.readOnlyRange = range;
                render();
            } else {
                if (typeof(self.onerror) === 'function') {
                    self.onerror(self, "Invalid range options");
                }
            }
        }

        self.getData = function() {
            return self.data;
        }

        self.setData = function(data, saveHistory) {

            if (typeof (self.onbeforechange) === 'function') {
                let ret = self.onbeforechange(self, { action: 'setData', data: data });
                if (ret === false) {
                    return false;
                }
            }

            if (saveHistory === true) {
                History.call(self, {
                    action: 'setData',
                    newData: JSON.parse(JSON.stringify(data)),
                    oldData: JSON.parse(JSON.stringify(self.data)),
                });
            }

            self.data = data || [];

            render();

            if (typeof (self.onchange) == 'function') {
                self.onchange(self);
            }
        }

        self.getEvent = function(guid) {
            const record = self.data.find((evt) => evt.guid === guid);
            if (!record) {
                return null;
            }
            return getDomByGuid(record);
        }

        self.render = function() {
            render();
        }

        self.undo = function() {
            History.undo.call(self);
        }

        self.redo = function() {
            History.redo.call(self);
        }

        self.next = function() {
            let currentDate = new Date(self.value);

            if (self.type === 'week' || self.type === 'weekdays') {
                // Navigate to next week (add 7 days)
                currentDate.setDate(currentDate.getDate() + 7);
            } else {
                // Navigate to next day (add 1 day)
                currentDate.setDate(currentDate.getDate() + 1);
            }

            self.value = currentDate.toISOString().substring(0, 10);
            render();
        }

        self.prev = function() {
            let currentDate = new Date(self.value);

            if (self.type === 'week' || self.type === 'weekdays') {
                // Navigate to previous week (subtract 7 days)
                currentDate.setDate(currentDate.getDate() - 7);
            } else {
                // Navigate to previous day (subtract 1 day)
                currentDate.setDate(currentDate.getDate() - 1);
            }

            self.value = currentDate.toISOString().substring(0, 10);
            render();
        }

        self.today = function() {
            let currentDate = new Date();
            currentDate.setDate(currentDate.getDate());
            self.value = currentDate.toISOString().substring(0, 10);
            render();
        }

        const updateBoard = function() {
            let count = [];
            for (let i = 1; i < self.headers.length; i++) {
                let x = self.headers[i].el.getAttribute('data-day');
                board[x] = [];
                for (let j = 0; j < totalDivisionsByDay; j++) {
                    if (self.tbody.children[j].children[i].children.length) {
                        for (let z = 0; z < self.tbody.children[j].children[i].children.length; z++ ) {
                            if (self.tbody.children[j].children[i].children[z] !== this.element) {
                                let t = getDuration(self.tbody.children[j].children[i].children[z]);
                                if (t) {
                                    count.push(t+1);
                                }
                            }
                        }
                    }

                    if (count.length) {
                        for (let z = 0; z < count.length; z++) {
                            count[z]--;
                        }
                        // Remove zeros
                        count = count.filter(n => n);
                        // Count number of events in each part of the grid
                        board[x][j] = count.length;
                    } else {
                        board[x][j] = 0;
                    }
                }
            }
        }

        const hasEvent = function(x, y1, y2) {
            if (board && board.length && board[x]) {
                for (let j = y1; j < y2; j++) {
                    if (board[x][j]) {
                        return true;
                    }
                }
            }
            return false;
        }

        const isInDisabledRange = function(y1, y2) {
            if (self.readOnlyRange && self.readOnlyRange.length > 0) {
                // Check if it's a single range ['08:00', '18:00'] or multiple ranges [['00:00', '08:00'], ['18:00', '23:59']]
                let ranges = Array.isArray(self.readOnlyRange[0]) ? self.readOnlyRange : [self.readOnlyRange];

                for (let k = 0; k < ranges.length; k++) {
                    if (ranges[k].length === 2) {
                        let r1 = hourToInt(ranges[k][0]) || 0;
                        let r2 = hourToInt(ranges[k][1]) || totalDivisionsByDay;

                        // Check if the event range overlaps with this disabled range
                        // Overlap occurs if: (y1 < r2 && y2 > r1)
                        if (y1 < r2 && y2 > r1) {
                            return true;
                        }
                    }
                }
            }
            return false;
        }

        const hasEventConflict = function(record, newValue) {
            // Get the time range for the updated event
            let start = newValue.start !== undefined ? newValue.start : record.start;
            let end = newValue.end !== undefined ? newValue.end : record.end;
            let y1 = hourToInt(start);
            let y2 = hourToInt(end);

            // Get the date/weekday for the updated event
            let dateOrWeekday;
            if (self.weekly) {
                dateOrWeekday = newValue.weekday !== undefined ? newValue.weekday : record.weekday;
            } else {
                dateOrWeekday = newValue.date !== undefined ? newValue.date : record.date;
                dateOrWeekday = dateOrWeekday.substring(0, 10);
            }

            // Check all other events for conflicts
            for (let i = 0; i < self.data.length; i++) {
                let evt = self.data[i];

                // Skip the current event being edited
                if (evt.guid === record.guid) {
                    continue;
                }

                // Check if event is in the same column (same day/weekday)
                let evtDateOrWeekday;
                if (self.weekly) {
                    evtDateOrWeekday = evt.weekday;
                } else {
                    evtDateOrWeekday = evt.date.substring(0, 10);
                }

                // If in the same column, check for time overlap
                if (evtDateOrWeekday === dateOrWeekday) {
                    let evtY1 = hourToInt(evt.start);
                    let evtY2 = hourToInt(evt.end);

                    // Check if time ranges overlap
                    if (!(y2 <= evtY1 || y1 >= evtY2)) {
                        return true;
                    }
                }
            }

            return false;
        }

        const getButton = function(e) {
            e = e || window.event;
            if (typeof e.buttons !== 'undefined') {
                return e.buttons;
            } else if (e.which) {
                return e.which;
            }
        }

        onload(() => {
            if (self.grid > 9) {
                self.el.classList.add('lm-schedule-large');
            }

            if (! self.value) {
                self.value = new Date().toISOString().substring(0, 10);
            }

            // Normalize initial data if provided (add guids, end times, etc.)
            if (self.data.length > 0) {
                normalizeEvents(self.data, self.value);
            }

            const dblClick = function(e) {
                if (e.target && isEvent(e.target)) {
                    // Cannot change readonly events
                    if (e.target.getAttribute('data-readonly') === 'true') {
                        return false;
                    }
                    if (self.ondblclick) {
                        self.ondblclick(self, e.target.event);
                    }
                    if (self.onedition) {
                        self.onedition(self, e.target.event);
                    }
                }
            }

            const mouseDown = function(e) {
                let button = getButton(e);
                if (button === 1) {
                    // Deselect events
                    self.resetSelection(e);

                    if (e.target.tagName === 'TD') {
                        // Cannot create events from disabled area
                        if (e.target.classList.contains('lm-schedule-disabled')) {
                            return false;
                        }

                        let x = e.target.getAttribute('data-x');
                        let y = e.target.getAttribute('data-y');

                        if (x != null && y != null) {
                            // Create a new event
                            state = {};
                            state.action = 'newEvent';
                            state.x = x;
                            state.y1 = parseInt(y);
                            // Initial size honours `snap` (defaults to 1 division)
                            state.y2 = Math.min(state.y1 + getSnapDivisions(), totalDivisionsByDay);
                            if (!self.weekly) {
                                x = e.target.getAttribute('data-date');
                            }
                            // Create a blank event
                            let event = createEmptyEventObject(x);

                            if (typeof(self.onbeforeinsert) === 'function') {
                                let ret = self.onbeforeinsert(self, event);
                                if (ret === false) {
                                    state = null;
                                    return false;
                                } else if (ret) {
                                    event = ret;
                                }
                            }

                            // Define the initial hour based on the click
                            event.start = intToHour(state.y1);
                            event.end = intToHour(state.y2);

                            // Create a blank DOM event element
                            state.event = event;
                            state.element = createEventElement(event, e.target);

                            // Selection
                            updateSelection(state.element);
                        }
                    } else if (e.target && isEvent(e.target)) {
                        // Cannot change readonly events
                        if (e.target.getAttribute('data-readonly') === 'true') {
                            return false;
                        }

                        let action = self.el.style.cursor;
                        if (action) {
                            state = {};
                            state.action = action;
                            state.x = e.target.parentNode.getAttribute('data-x');
                            state.y1 = hourToInt(e.target.event.start);
                            state.y2 = hourToInt(e.target.event.end) - 1;
                            state.element = e.target;
                            state.event = e.target.event;

                            // Update the label from the DIV
                            updateLabel(state);
                        }
                        // Selection
                        updateSelection(e.target);
                    }

                    if (self.onbeforechangeevent) {
                        let ret = self.onbeforechangeevent(self, state);
                        if (ret === false) {
                            state = null;
                            return false;
                        }
                    }

                    // Create board limits
                    if (state && state.action && ! self.overlap) {
                        updateBoard.call(state);
                    }
                }
            }

            const mouseMove = function(e) {
                // Mouse over an event
                if (! state) {
                    if (isEvent(e.target)) {
                        let rect = e.target.getBoundingClientRect();
                        if (rect.height - (e.clientY - rect.top) < 5) {
                            self.el.style.cursor = 's-resize';
                        } else if (e.clientY - rect.top < 25) {
                            self.el.style.cursor = 'move';
                        } else {
                            self.el.style.cursor = '';
                        }
                    } else {
                        self.el.style.cursor = '';
                    }
                } else {
                    // Get the element the mouse is over
                    let reference = findElement(document.elementsFromPoint(e.clientX, e.clientY))
                    if (reference) {
                        // Get row
                        let y = parseInt(reference.getAttribute('data-y'));
                        // Get the column
                        let x = parseInt(reference.getAttribute('data-x'));

                        // Actions to be performed
                        if (state.action === 'move') {
                            let eventHeight = (state.y2 - state.y1) + 1;
                            let newY2 = y + eventHeight;

                            // Check if moving into disabled area
                            if (isInDisabledRange(y, newY2)) {
                                return false;
                            }

                            // Check limits
                            if (! self.overlap && hasEvent(x, y, newY2)) {
                                return false;
                            }

                            reference.appendChild(state.element);
                            state.y1 = y;
                            state.y2 = parseInt(Math.ceil(state.element.offsetHeight / minutesPerDivision) + parseInt(state.y1)) - 1;

                            // Update the label from the DIV
                            updateLabel(state);
                        } else {
                            let y1,y2,h,t;

                            // Snap the resize target so the event size is a
                            // multiple of `snap` (no-op when snap == grid).
                            let snappedY = snapResizeY(y);

                            // Determine the new time range
                            if (state.y1 < snappedY) {
                                y1 = state.y1;
                                y2 = snappedY + 1;
                            } else {
                                y1 = snappedY;
                                y2 = state.y1 + 1;
                            }

                            // Check if resizing into disabled area
                            if (isInDisabledRange(y1, y2)) {
                                return false;
                            }

                            // Check limits
                            if (! self.overlap) {
                                if (hasEvent(state.x, y1, y2)) {
                                    return false;
                                }
                            }

                            // Resize
                            state.y2 = snappedY;

                            // Position from top
                            let h1 = self.tbody.children[state.y1].offsetTop;
                            let h2 = self.tbody.children[state.y2].offsetTop;
                            let u = self.tbody.children[state.y1].offsetHeight;

                            if (state.y2 > state.y1) {
                                h = h2 - h1;
                                t = 0;
                            } else {
                                h = h1 - h2;
                                t = -1 * h;
                            }

                            h += u;

                            if (h > 0) {
                                state.element.style.top = t + 'px';
                                state.element.style.height = h + 'px';

                                // Update the label from the DIV
                                updateLabel(state);
                            }
                        }
                    } else {
                        if (state.action === 'move' && state.element.parentNode) {
                            document.body.style.cursor = 'not-allowed';
                        }
                    }
                }
            }

            const mouseUp = function(e) {
                // Call event
                if (state && state.element) {
                    // Remove element
                    if (! state.element.parentNode) {
                        // Do nothing
                    } else {
                        if (parseInt(state.element.style.top) < 0) {
                            state.element.style.top = '0px';
                            // Get the element the mouse is over
                            let reference = findElement(document.elementsFromPoint(e.clientX, e.clientY));
                            if (reference) {
                                reference.appendChild(state.element);
                            }
                        }

                        // Events
                        if (state.action === 'newEvent') {
                            if (! state.element.start) {
                                // Remove element
                                state.element.remove();
                                state.element = null;
                            } else {
                                // Finalize edition and create the new event
                                state.event.start = state.element.start;
                                state.event.end = state.element.end;
                                // Create event
                                self.addEvents([state.event], e);
                            }
                        } else if (state.action) {
                            // Day
                            let d = self.weekly ? state.element.event.weekday === state.element.weekday : state.element.event.date === state.element.date;
                            // Verify changes
                            if (d && state.element.event.start === state.element.start && state.element.event.end === state.element.end) {
                                // Nothing changed
                            } else {
                                let record = {
                                    start: state.element.start,
                                    end: state.element.end,
                                }

                                if (self.weekly) {
                                    record.weekday = parseInt(state.element.weekday);
                                } else {
                                    record.date = state.element.date;
                                }

                                self.updateEvent(state.element.event, record);
                            }
                        }
                    }
                }

                // Remove any possible cursor
                if (document.body.style.cursor === 'not-allowed') {
                    document.body.style.cursor = '';
                }

                // Destroy state
                state = null;
            }

            const keyDown = function(e) {
                // History
                if (e.ctrlKey && e.key === 'z') {
                    History.undo.call(self);
                } else if (e.ctrlKey && e.key === 'y') {
                    History.redo.call(self);
                } else if (e.ctrlKey && e.key === 'v') {
                    if (pasteHistory.length) {
                        let records = pasteHistory.map((v) => {
                            let event = Object.assign({}, v);
                            event.guid = guid();
                            event.start = intToHour(1 + hourToInt(event.start));
                            event.end = intToHour(1 + hourToInt(event.end));
                            return event;
                        });

                        self.addEvents(records, e);
                    }
                } else  if (document.activeElement === self.el) {
                    if (e.keyCode === 46) {
                        // Add to the selected events
                        if (selected.length) {
                            let records = [];
                            for (let i = 0; i < selected.length; i++) {
                                records.push(selected[i].guid);
                            }
                            self.deleteEvents(records);
                        }
                    } else if (e.keyCode === 37 || e.keyCode === 38) {
                        changeLeftEventFocus();
                    } else if (e.keyCode === 39 || e.keyCode === 40) {
                        changeRightEventFocus();
                    }

                    // Copy and Paste
                    if (e.key === 'c' && e.ctrlKey) {
                        pasteHistory.length = 0;
                        pasteHistory = selected.map(a => ({ ...a }));
                    }
                }
            }

            self.el.addEventListener('keydown', keyDown);
            self.el.addEventListener('dblclick', dblClick)
            self.el.addEventListener('mousedown', mouseDown);

            document.addEventListener('mousemove', mouseMove);
            document.addEventListener('mouseup', mouseUp);

            render();
        })

        onchange((prop) => {
            if (prop === 'type' || prop === 'grid' || prop === 'weekly' || prop === 'value' || prop === 'data') {
                render();
            }
        });

        track('type');
        track('grid');
        track('weekly');
        track('data');

        return render => render`<div class="lm-schedule" tabindex="0">
            <div class="lm-schedule-pointer" :ref="self.pointer"></div>
            <table>
                <thead><tr :loop="self.headers"><td data-day="{{self.day}}" data-weekday="{{self.weekday}}" data-selected="{{self.selected}}">{{self.value}}</td></tr></thead>
                <tbody :ref="self.tbody"></tbody>
            </table>
        </div>`;
    }

    lemonade.setComponents({ Schedule: Schedule });

    // Register the web component
    lemonade.createWebComponent('lm-schedule', Schedule);

    return function (root, options) {
        if (typeof (root) === 'object') {
            lemonade.render(Schedule, root, options)
            return options;
        } else {
            return Schedule.call(this, root)
        }
    }
})));


/***/ }),

/***/ 910:
/***/ (function(module, __unused_webpack_exports, __webpack_require__) {



if (! utils && "function" === 'function') {
    var utils = __webpack_require__(91);
}

; (function (global, factory) {
     true ? module.exports = factory() :
    0;
}(this, (function () {

    let dateSignature = null;

    // Dispatcher
    const Dispatch = function (type, ...args) {
        if (typeof this[type] === 'function') {
            this[type](this, ...args);
        }
    }

    const extractFromHtml =  function(element) {
        let data = [];
        // Content
        for (let i = 0; i < element.children.length; i++) {
            let e = element.children[i];
            let item = {
                title: e.textContent || e.getAttribute('title') || '',
                date: e.getAttribute('data-date'),
                borderColor: e.getAttribute('data-color') || '',
                borderStyle: e.getAttribute('data-style') || '',
            }
            data.push(item);
        }

        return data;
    }

    const extract = function(children) {
        let data = [];

        if (this.tagName) {
            data = extractFromHtml(this);

            // Remove all elements
            this.textContent = '';

            if (!Array.isArray(this.data)) {
                this.data = [];
            }

            if (data && data.length) {
                // Compatibility legacy jsuites
                data.forEach((v) => {
                    this.data.push(data);
                });
            }
        }
    }

    const Timeline = function (children, { onload, onchange, track }) {
        let self = this;

        extract.call(this, children);

        const toDate = function(d) {
            return d instanceof Date ? d : new Date(d);
        }

        let date = self.value ? toDate(self.value) : new Date();

        self.result = [];

        if (!Array.isArray(self.data)) {
            self.data = [];
        }

        if (! self.format) {
            if (self.type === 'monthly') {
                self.format = 'dd mmm yyyy';
            } else {
                self.format = 'dddd, dd';
            }
        }

        self.year = date.getFullYear();
        self.month = 1 + date.getMonth();
        self.months = utils.Helpers.months;

        // Error message
        if (! self.message) {
            self.message = 'No records found';
        }

        if (! self.order) {
            self.order = 'asc';
        }

        // Make sure to align has a default
        if (!['top', 'right', 'bottom', 'left'].includes(self.align)) {
            self.align = 'left';
        }

        if (typeof self.controls === 'undefined') {
            self.controls = self.type === 'monthly';
        }

        self.next = function () {
            if (self.month === 12) {
                self.year++;
                self.month = 1;
            } else {
                self.month++;
            }
        }

        self.prev = function () {
            if (self.month === 1) {
                self.year--;
                self.month = 12;
            } else {
                self.month--;
            }
        }

        const isRemote = function() {
            return self.remote && self.url && self.type === 'monthly';
        }

        const getDate = function(d) {
            let date = d && d === dateSignature ? '' : d;
            dateSignature = d;
            return date;
        }

        const updateResult = function () {
            let result = [];

            if (self.type === 'monthly') {
                for (let i = 0; i < self.data.length; i++) {
                    let d = toDate(self.data[i].date);
                    if ((d.getMonth() + 1) === self.month && d.getFullYear() === self.year) {
                        result.push(self.data[i]);
                    }
                }
            } else {
                result = self.data;
            }

            result = result.sort((a, b) => (self.order === 'desc' ? -1 : 1) * (toDate(a.date).getTime() - toDate(b.date).getTime()));

            for (let i = 0; i < result.length; i++) {
                result[i].day = utils.Mask.render(result[i].date, self.format);
            }

            self.result = result;

            // Reset the date signature to avoid interference in the next rendering
            dateSignature = null;

            // Event
            Dispatch.call(self, 'onupdate', result);
        }

        const fetchRemote = function () {
            const xhr = new XMLHttpRequest();

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        let res = JSON.parse(xhr.responseText);

                        let result = [];
                        if (Array.isArray(res.result)) {
                            result = res.result;
                        } else if (Array.isArray(res)) {
                            result = res
                        }

                        for (let i = 0; i < result.length; i++) {
                            result[i].date = new Date(result[i].date);
                            result[i].day = getDate(result[i].date.toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: '2-digit' }));
                        }
                        
                        if (isRemote()) {
                            self.result = result;
                        } else {
                            self.data = result;
                        }
                    } else {
                        console.error('Failed to fetch data. Status code: ' + xhr.status);
                    }
                }
            };

            let url = self.url;

            if (isRemote()) {
                url += `?year=${self.year}&month=${self.month}`;
                url += `&asc=${self.order === 'asc'}`
            }

            xhr.open('GET', url, true);
            xhr.setRequestHeader('Content-Type', 'text/json')
            xhr.send();
        }

        const updateBorders = function() {
            self.result.forEach(entry => {
                if (entry.borderColor) {
                    entry.el.style.setProperty('--lm-border-color', entry.borderColor);
                }
                if (entry.borderStyle) {
                    entry.el.style.setProperty('--lm-border-style', entry.borderStyle);
                }
                if (Array.isArray(entry.tags) && entry.tags.length) {
                    const tagEls = entry.el.querySelectorAll('.lm-timeline-tag');
                    entry.tags.forEach((tag, i) => {
                        if (tagEls[i] && tag.color) {
                            tagEls[i].style.backgroundColor = tag.color;
                        }
                    });
                }
            });
        }

        const edition = function(e, s) {
            if (typeof self.onedition === 'function') {
                self.onedition(s);
            }
        }

        const tagClick = function(e, s) {
            if (s.onclick) {
                s.onclick(e, s);
            }
        }
        onchange((prop) => {
            if (prop === 'value') {
                date = toDate(self.value);
                self.year = date.getFullYear();
                self.month = 1 + date.getMonth();
            } else if (prop === 'data' || prop === 'month' || prop === 'order') {
                if (isRemote()) {
                    fetchRemote();
                } else {
                    updateResult();
                }
            } else if (prop === 'result') {
                updateBorders();
            }
        })

        onload(() => {
            if (self.url) {
                fetchRemote();
            } else {
                updateResult();
            }

            if (typeof(self.width) !== 'undefined') {
                self.el.style.width = parseInt(self.width) + 'px';
            }
            if (typeof(self.height) !== 'undefined') {
                self.el.style.height = parseInt(self.height) + 'px';
            }
        });

        track('data');
        track('order');

        return render => render`<div class="lm-timeline">
            <div class="lm-timeline-header" data-visible="{{self.controls}}" data-type="{{self.type}}">
                <div class="lm-timeline-label">
                    <div class="lm-timeline-year">${self.year}</div>
                    <div class="lm-timeline-month">${self.months[self.month - 1]}</div>
                </div>
                <div class="lm-timeline-navigation">
                    <button type="button" class="lm-timeline-icon lm-ripple" onclick="${self.prev}" tabindex="0">expand_less</button>
                    <button type="button" class="lm-timeline-icon lm-ripple" onclick="${self.next}" tabindex="0">expand_more</button>
                </div>
            </div>
            <div :loop="self.result" data-message="{{self.message}}" data-mode="{{self.position}}" data-align="{{self.align}}" class="lm-timeline-data">
                <div class="lm-timeline-item" data-bullet="{{self.day}}">
                    <div class="lm-timeline-edit" :render="self.editable"><button type="button" class="lm-timeline-icon lm-ripple lm-cursor" onclick="${edition}" tabindex="0">edit</button></div>
                    <div class="lm-timeline-title">{{self.title}}</div>
                    <div class="lm-timeline-subtitle">{{self.subtitle}}</div>
                    <div class="lm-timeline-description">{{self.description}}</div>
                    <div class="lm-timeline-tags" :loop="self.tags">
                        <span class="lm-timeline-tag" onclick="${tagClick}">{{self.title}}</span>
                    </div>
                </div>
            </div>
        </div>`;
    }

    lemonade.setComponents({ Timeline: Timeline });

    // Register the web component
    lemonade.createWebComponent('timeline', Timeline);

    return function (root, options) {
        if (typeof (root) === 'object') {
            lemonade.render(Timeline, root, options);
            return options;
        } else {
            return Timeline.call(this, root);
        }
    }
})));

/***/ }),

/***/ 926:
/***/ (function(module) {

"use strict";
module.exports = lemonade;

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	!function() {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = function(module) {
/******/ 			var getter = module && module.__esModule ?
/******/ 				function() { return module['default']; } :
/******/ 				function() { return module; };
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	}();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	!function() {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = function(exports, definition) {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	}();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	!function() {
/******/ 		__webpack_require__.o = function(obj, prop) { return Object.prototype.hasOwnProperty.call(obj, prop); }
/******/ 	}();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry needs to be wrapped in an IIFE because it needs to be in strict mode.
!function() {
"use strict";
/* harmony import */ var _plugins_calendar_dist_index__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(673);
/* harmony import */ var _plugins_calendar_dist_index__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_plugins_calendar_dist_index__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _plugins_timeline_dist_index__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(910);
/* harmony import */ var _plugins_timeline_dist_index__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_plugins_timeline_dist_index__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _plugins_schedule_dist_index__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(108);
/* harmony import */ var _plugins_schedule_dist_index__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_plugins_schedule_dist_index__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _plugins_schedule_dist_event__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(256);
/* harmony import */ var _plugins_schedule_dist_event__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_plugins_schedule_dist_event__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _jsuites_utils__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(91);
/* harmony import */ var _jsuites_utils__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_jsuites_utils__WEBPACK_IMPORTED_MODULE_4__);











let about = function () {
    return {
        name: 'CalendarJS CE',
        version: '1.0.0',
        url: 'https://calendarjs.com/',
    };
};

const setDictionary = function(d) {
    if (! document.dictionary) {
        document.dictionary = {}
    }
    // Replace the key into the dictionary and append the new ones
    let k = Object.keys(d);
    for (let i = 0; i < k.length; i++) {
        document.dictionary[k[i]] = d[k[i]];
    }
}

let calendarjs = {
    Calendar: (_plugins_calendar_dist_index__WEBPACK_IMPORTED_MODULE_0___default()),
    Timeline: (_plugins_timeline_dist_index__WEBPACK_IMPORTED_MODULE_1___default()),
    Schedule: (_plugins_schedule_dist_index__WEBPACK_IMPORTED_MODULE_2___default()),
    Event: (_plugins_schedule_dist_event__WEBPACK_IMPORTED_MODULE_3___default()),
    Helpers: (_jsuites_utils__WEBPACK_IMPORTED_MODULE_4___default().Helpers),
    setDictionary: setDictionary,
    about: about,
}

/* harmony default export */ __webpack_exports__["default"] = (calendarjs);
}();
calendarjs = __webpack_exports__["default"];
/******/ })()
;

    return calendarjs;
})));