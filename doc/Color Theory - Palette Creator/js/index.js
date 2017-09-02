/* jshint esversion: 6 */

// This is using Sass.js to use Sass built-in color mixing functions

const firstColorChooser = document.forms['color-theory']['first-color'];
const firstColor = document.querySelector('.first-color');
const secondColor = document.querySelector('.second-color');

let hue = undefined;
let comp = undefined;

updateColors();
Sass.options({
  precision: 1
});
computeScss();

document.forms['color-theory']['first-color'].addEventListener('input', updateColors);

document.forms['color-theory']['first-color'].addEventListener('change', computeScss);

function updateColors(ev) {
  hue = parseInt(firstColorChooser.value);
  comp = (hue + 180) % 360;
  setColorPreview([firstColor], `hsl(${hue}, 100%, 50%)`);
  setColorPreview([secondColor], `hsl(${comp}, 100%, 50%)`);
}

function setColorPreview(fieldsets, color) {
  Array.from(fieldsets).forEach(fieldset => {
    const preview = fieldset.querySelector('.color-preview');
    preview.style.backgroundColor = fieldset.querySelector('.color-code').value = color;
    const text = fieldset.querySelector('.color-text')
    if(text)
      text.style.color = computeTextColor(window.getComputedStyle(preview).backgroundColor);
  });
}

function setColorText(fieldsets, bg, text) {
  Array.from(fieldsets).forEach(fieldset => {
    fieldset.querySelector('.color-preview').style.backgroundColor = bg;
    fieldset.querySelector('.color-text').style.color = fieldset.querySelector('.color-code').value = text;
  });
}

function computeScss() {
  Sass.compile(
    `$first-color: hsl(${hue}, 100%, 50%);` +
    document.querySelector('#scss-template').content.firstElementChild.textContent, computedScssHandler);

}

function computedScssHandler(result) {
  let colors = {};
  result.text.split('\n\n').forEach(rule => {
    const color = /\.([\w\-]+) {\s*color: (hsl\() (\d{1,3}(?:\.\d+)?)deg(.*) (\));\s*}/.exec(rule).splice(1, 5).join('').split('hsl');
    colors[color[0]] = `hsl${color[1]}`;
  });

  for (let colorName in colors)
    if (document.querySelector(`.${colorName}`)) setColorPreview(document.querySelectorAll(`.${colorName}`), colors[colorName]);

  const primaryTextColor = computeTextColor(window.getComputedStyle(document.querySelector('.primary-color .color-preview')).backgroundColor);
  const complementaryTextColor = computeTextColor(window.getComputedStyle(document.querySelector('.complementary-color .color-preview')).backgroundColor);
  setColorText([document.querySelector('.text-on-primary')], document.querySelector('.primary-color .color-preview').style.backgroundColor, primaryTextColor);
  setColorText([document.querySelector('.text-on-complementary')], document.querySelector('.complementary-color .color-preview').style.backgroundColor, complementaryTextColor)
}

function computeTextColor(colorStr) {
  const black = [0, 0, 0, .87];
  const white = [255, 255, 255, 1];

  [, , r, g, b, a] = /(rgba?)\((\d{1,3}), (\d{1,3}), (\d{1,3})(?:, (\d(?:\.\d+)))?\)/.exec(colorStr);
  const color = [parseInt(r), parseInt(g), parseInt(b), parseFloat(a == undefined ? 1 : a)]
  const blackContrast = computeConstrastRatio(black, color);
  const whiteContrast = computeConstrastRatio(white, color);
  return blackContrast < whiteContrast ? `hsl(0, 0%, 100%)` : `hsla(0, 0%, 0%, 0.87)`
}

function computeConstrastRatio([fr, fg, fb, fa], [br, bg, bb, ba]) {
  if (fa < 1) {
    fr = fr * fa + br * (1 - fa);
    fg = fg * fa + bg * (1 - fa);
    fb = fb * fa + bb * (1 - fa);
    fa = 1;
  }
  const fl = luminance([fr, fg, fb]);
  const bl = luminance([br, bg, bb]);

  if (fl < bl)
    return (bl + .05) / (fl + .05);
  else
    return (fl + .05) / (bl + .05);
}

function luminance([r, g, b]) {
  return .2126 * colorComponent(r) + .7152 * colorComponent(g) + .0722 * colorComponent(b);
}

function colorComponent(color) {
  const c = color / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}