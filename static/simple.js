const nillebAnalytics = {
    analyticsEndpoint: '{{base_url}}{{API_PREFIX}}{{ANALYTICS_API}}/collect?property_id={{ request.query_params["pid"] }}',
    trackEvent: function(event) {
        fetch(this.analyticsEndpoint,  {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                page_url: window.location.href,
                referrer: document.referrer,
                event: event
            })
        });
    }
};

nillebAnalytics.trackEvent('page_view');
