# WebPageTest: web vitals audit

Verify options against the WebPageTest version and plan in use.

## Running
- Choose the location, device, browser, and connectivity profile that match your users. Set several runs (for example 5 to 9) and read the median run.
- Test first view (cold cache) and repeat view (warm cache) separately when both matter.
- Use scripting or multi-step tests for journeys beyond the first page.

## Notes
- Read the waterfall for request chains, blocking resources, and connection setup. The filmstrip and video show when content appears to the user.
- Use the web vitals and the "LCP element" information to find what the largest contentful paint was, and the layout shift view to find shifting elements.
- Compare runs side by side to check a change under identical conditions.
- Third-party request breakdown shows which hosts cost the most time and bytes.
- API usage normally needs a key. Do not commit keys.
