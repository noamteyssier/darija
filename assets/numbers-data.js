const UNITS = [null, ['wa7ed', 'واحد'], ['juj', 'جوج'], ['tlata', 'تلاتة'], ['rb3a', 'ربعة'], ['khamsa', 'خمسة'], ['setta', 'ستة'], ['sb3a', 'سبعة'], ['tmanya', 'تمنية'], ['ts3ud', 'تسعود'],
  ['3achra', 'عشرة'], ['7dach', 'حداش'], ['tnach', 'طناش'], ['tlettach', 'تلطاش'], ['rb3tach', 'ربعطاش'], ['khamstach', 'خمسطاش'], ['settach', 'سطاش'], ['sb3tach', 'سبعطاش'], ['tmentach', 'تمنطاش'], ['ts3tach', 'تسعطاش']];
const TENS = [null, null, ['3achrin', 'عشرين'], ['tlatin', 'تلاتين'], ['rb3in', 'ربعين'], ['khamsin', 'خمسين'], ['settin', 'ستين'], ['sb3in', 'سبعين'], ['tmanin', 'تمانين'], ['ts3in', 'تسعين']];
// Hundreds from 300 and thousands from 3000 use these short stems: tlt mya, tlt alaf.
const STEM = { 3: ['tlt', 'تلت'], 4: ['rb3', 'ربع'], 5: ['khms', 'خمس'], 6: ['stt', 'ست'], 7: ['sb3', 'سبع'], 8: ['tmn', 'تمن'], 9: ['ts3', 'تسع'], 10: ['3achr', 'عشر'] };

// 0 to 10000. Parts (thousands, hundreds, then units and tens) are joined with "w" (and).
export function say(n) {
  if (!n) return { lat: 'sifr', ar: 'صفر' };
  const parts = [];
  const th = Math.floor(n / 1000), h = Math.floor(n % 1000 / 100), r = n % 100;
  if (th) parts.push(th === 1 ? ['alf', 'ألف'] : th === 2 ? ['alfin', 'ألفين'] : [STEM[th][0] + ' alaf', STEM[th][1] + ' ألاف']);
  if (h) parts.push(h === 1 ? ['mya', 'مية'] : h === 2 ? ['mitin', 'ميتين'] : [STEM[h][0] + ' mya', STEM[h][1] + ' مية']);
  if (r && r < 20) parts.push(UNITS[r]);
  else if (r) {
    // 2 is tnin beside a ten (tnin w 3achrin), juj on its own.
    if (r % 10) parts.push(r % 10 === 2 ? ['tnin', 'تنين'] : UNITS[r % 10]);
    parts.push(TENS[Math.floor(r / 10)]);
  }
  return { lat: parts.map(p => p[0]).join(' w '), ar: parts.map(p => p[1]).join(' و ') };
}

const EN_UNITS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'];
const EN_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];
// English name for the round numbers the dictionary lists: 0-19, tens, hundreds, thousands.
export function english(n) {
  return n < 20 ? EN_UNITS[n] : n < 100 ? EN_TENS[n / 10] : n < 1000 ? EN_UNITS[n / 100] + ' hundred' : EN_UNITS[n / 1000] + ' thousand';
}
