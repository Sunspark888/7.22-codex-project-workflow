(() => {
 const b=document.getElementById('menu-toggle'), nav=document.querySelector('.topbar nav');
 if(b&&nav){b.addEventListener('click',()=>{const open=nav.classList.toggle('open');b.setAttribute('aria-expanded',open?'true':'false');b.setAttribute('aria-label',open?'收起导航':'展开导航')});nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');b.setAttribute('aria-expanded','false')}));}
})();