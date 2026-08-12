# Data Policy

## Real data

Use only data you are authorized to access through official APIs or other permitted sources.

## Synthetic demo data

`data/generated/demo_posts.csv` is synthetic. It exists only to make the application runnable before API credentials are configured.

Never describe synthetic values as:
- real voter sentiment
- real public opinion
- real engagement
- real statements by an MLA

## Account verification

Before adding a social handle or channel ID:
1. Check the official MLA/party/government website or the platform's verified/official profile.
2. Record the source used for verification.
3. Set `official_account_verified=YES` only after verification.

## Political neutrality

This dashboard is an analytics/engineering demonstration. It should not be used to target, manipulate, persuade, or profile individual voters.
