const a7s = {
    analyticsEndpoint: '{{base_url}}{{API_PREFIX}}{{ANALYTICS_API}}/collect?property_id={{ request.query_params["pid"] }}',
    trackEvent: function(event) {
        fetch(this.analyticsEndpoint,  {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                page_url: window.location.href,
                event: event
            })
        });
    }
};

a7s.trackEvent('page_view');

window.nillebAnalytics = a7s;
