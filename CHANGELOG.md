# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [5.3.1](https://github.com/GetStream/stream-python/compare/v5.2.1...v5.3.1) (2023-10-25)

### [5.2.1](https://github.com/GetStream/stream-python/compare/v5.2.0...v5.2.1) (2023-02-27)

## [5.2.0](https://github.com/GetStream/stream-python/compare/v5.1.1...v5.2.0) (2023-02-16)


### Features

* add support for 3.11 ([2eae7d7](https://github.com/GetStream/stream-python/commit/2eae7d7958f3b869982701188fc0d04a5b8ab021))
* added async support ([b4515d3](https://github.com/GetStream/stream-python/commit/b4515d337be88ff50ba1cbad8645b1fbc8862ce0))


### Bug Fixes

* tests and linting ([cfacbbc](https://github.com/GetStream/stream-python/commit/cfacbbcadf45ca91d3e6c2a310dfd6fea1a03146))
* redirect, uniqueness and deprecations ([aefdcd3](https://github.com/GetStream/stream-python/commit/aefdcd39ff8a41a443455f1a41cc819039015cdb))

## 5.1.1 - 2022-01-18

* Handle backward compatible pyjwt 1.x support for token generation

## 5.1.0 - 2021-04-16

* Add analytics support for `track_engagements` and `track_impressions`
* Update license to BSD-3 canonical description

## 5.0.1 - 2021-01-22

* Bump pyjwt to 2.x

## 5.0.0 - 2020-09-17

* Drop python 3.5 and add 3.9
* Improve install and CI

## 4.0.0 - 2020-09-02

* Drop old create_user_session_token in favor create_user_token
* Drop python support before 3.4
* Allow custom data in client.create_jwt_token
* Add kind filter for reactions in enrichment
* Add follow stat support
* Move to github actions from travis and improve static analysis
* Update readme for old docs
* Update some crypto dependencies

## 3.5.1 - 2020-06-08

* Handle warning in JWT decode regarding missing algorithm

## 3.5.0 - 2020-06-08

* Add enrichment support to direct activity get

## 3.4.0 - 2020-05-11

* Expose target_feeds_extra_data to add extra data to activities from reactions

## 3.3.0 - 2020-05-04

* Add batch unfollow support

## 3.2.1 - 2020-03-17

* Set timezone as utc in serialization hooks

## 3.2.0 - 2020-03-17

* Add open graph scrape support
* Update python support (drop 2.6, add 3.8)
* Fixes in docs for collections and personalization

## 3.1.1 - 2019-11-07

* Bump crypto deps

## 3.1.0 - 2018-05-24

* Batch partial update

## 3.0.2 - 2018-05-24

* Fixes for filtering by reactions by kind

## 3.0.1 - 2018-12-04

* Add short-hand version for collections.create_reference()

## 3.0.0 - 2018-12-03

* Add support for reactions
* Add support for users
* Removed HTTP Signatures based auth
* Use JWT auth for everything
* Add feed.get enrichment params

## 2.12.0 - 2018-10-08

* Add user-session-token support

## 2.11.0 - 2017-08-23

* Add collection helpers to create refs

## 2.10.0 - 2017-07-30

* Partial activity API endpoint

## 2.9.3 - 2017-07-20

* Use Readme.md content as package long description

## 2.9.2 - 2017-07-20

* Fixed deserialization problem with datetime objects with zeroed microseconds
* Support newer versions of the pyJWT lib

## 2.9.1 - 2017-07-18

Renamed client.get_activities' foreign_id_time param to foreign_id_times

## 2.9.0 - 2017-07-05

* Add support for get activity API endpoint

## 2.8.1 - 2017-12-21

* Fixes a regression with embedded httpsig and Python 3

## 2.8.0 - 2017-12-21

* Fixes install issues on Windows
* Bundle http-sig library
* Use pycryptodomex instead of the discontinued pycrypto library

## 2.7.0 - 2017-12-14

* All client methods that make requests will return the response

## 2.6.2 - 2017-12-08

* Consolidate API URL generation across API, Collections and Personalization services

## 2.6.0 - 2017-12-08

Support the new collections endpoint and flexible get requests for personalization

## 2.5.0 - 2017-10-19

* Use new .com domain for API and Analytics

## 2.4.0 - 2017-08-31

* Added support for To target update endpoint

## 2.3.11 - 2017-05-22

* Added support for Python 2.6.9 and downgrade to requests 2.2.1

## 2.3.9 - 2016-12-20

* Fix errors_from_fields function so it displays the extra data returned by the
    server about InputException errors.

## 2.3.8 - 2016-06-09

* Add support for keep_history on unfollow

## 2.3.7 - 2016-06-02

* Add HTTP Signature auth method (for application auth resources)
* Add support for follow_many batch operation
* Add support for add_to_many batch operation
* Decode JWT from bytes to UTF-8
* Skip add_activities API call if activity_list is empty
* Fix feed group and id validation, dashes are now allowed

## 2.3.5 - 2015-10-07

* Added support for activity update

## 2.3.3 - 2015-10-07

* Added support for creating redirect urls

## 2.3.0 - 2015-06-11

* Added support for read-only tokens

## 2.1.4 - 2015-01-14

* Added support for extra data for follow actions

## 2.1.3 - 2015-01-05

* Bugfix, mark_seen and mark_read now work

## 2.1.0 - 2014-12-19

* Added location support to reduce latency

## 2.0.1 - 2014-11-18

* Additional validation on feed_slug and user_id

## 2.0.0 - 2014-11-10

* Breaking change: New style feed syntax, client.feed('user', '1') instead of client.feed('user:3')
* Breaking change: New style follow syntax, feed.follow('user', 3)
* API versioning support
* Configurable timeouts
* Python 3 support

## 1.1.1 - 2014-09-20

* Add HTTP client retries

## 1.1.0 -2014-09-08

* Add support for mark read (notifications feeds)
