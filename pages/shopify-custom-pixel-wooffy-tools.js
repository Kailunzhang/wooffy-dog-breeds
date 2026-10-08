// Wooffy tools -> GA4 custom pixel.
// Paste into Shopify admin: Settings -> Customer events -> Add custom pixel ("Wooffy tools to GA4").
// Permission: Analytics. Data sale: "Data collected does not qualify as data sale".
//
// Page views are already sent by the Google & YouTube app. This pixel only forwards the
// quiz and calculator events our pages publish with Shopify.analytics.publish():
//   wooffy_quiz_start         first answer           {quiz}
//   wooffy_quiz_complete      results shown          {quiz, top_breed, result_count}
//   wooffy_quiz_result_click  click on a result card {breed_slug, rank, link_type}
//   wooffy_calc_change        calculator changed     {event, breed, option, value}
const GA4_ID = 'G-9Z02JQG9M3';

const tag = document.createElement('script');
tag.async = true;
tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
document.head.appendChild(tag);
window.dataLayer = window.dataLayer || [];
function gtag() { window.dataLayer.push(arguments); }
gtag('js', new Date());
gtag('config', GA4_ID, { send_page_view: false });

// "value" is a reserved GA4 money parameter and "event" reads badly in reports, so rename them.
function params(name, data) {
  const d = data || {};
  if (name === 'wooffy_calc_change') {
    return { calc_action: d.event, breed: d.breed, option: d.option || undefined, option_value: d.value || undefined };
  }
  return d;
}

['wooffy_quiz_start', 'wooffy_quiz_complete', 'wooffy_quiz_result_click', 'wooffy_calc_change'].forEach((name) => {
  analytics.subscribe(name, (event) => {
    const loc = event.context && event.context.document && event.context.document.location;
    gtag('event', name, Object.assign({}, params(name, event.customData), { page_location: loc ? loc.href : undefined }));
  });
});
