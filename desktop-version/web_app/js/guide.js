(function(){
  "use strict";
  const builtin=window.PixelPlanetLocales;
  function applyLanguage(code){const locales=builtin,active=locales[code]?code:"zh-CN",messages=locales[active],fallback=builtin["zh-CN"],text=key=>messages[key]??fallback[key]??key;document.documentElement.lang=active;document.querySelectorAll("[data-i18n]").forEach(element=>{element.textContent=text(element.dataset.i18n)});const select=document.getElementById("language-select");select.textContent="";Object.entries(locales).forEach(([id,locale])=>select.add(new Option(locale["language.name"]||id,id)));select.value=active;try{localStorage.setItem("ppg-language",active)}catch{}}
  const select=document.getElementById("language-select");select.addEventListener("change",event=>applyLanguage(event.target.value));let language="zh-CN";try{language=localStorage.getItem("ppg-language")||language}catch{}applyLanguage(language);
})();
