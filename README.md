# lso-backend

lso-backend

## API Usage:

Base URL Development(Elastic Beanstalk CNAME): http://lsobackend-dev.us-west-2.elasticbeanstalk.com
Base URL Production(Elastic Beanstalk CNAME): http://lsobackend-prod.us-west-2.elasticbeanstalk.com

### Endpoints:

1. **Sign Up**
    * **URL**: `/auth/signup`
    * **Description**: To signup the user
    * **Method**: `POST`
    * **Required Payload**:
        * `username: String`,
        * `password: String`,
        * `first_name: String`,
        * `last_name: String`,
        * `business_name: String`,
        * `contact_number: String`,
        * `type_of_business: String`,
        * `country: String`,
        * `address: String`,
        * `address_2: String`,
        * `address_3: String`,
        * `postal_code: String`,
        * `city: String`,
        * `state: String`,
        * `packages_per_day: String`
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/signup" \
    -X POST \
    -d '{"username": "viraj@outliant.com", "password": "Abcd@1234", "first_name": "Viraj", "last_name": "Shah", "business_name": "Outliant", "contact_number": "987654321", "type_of_business": "IT", "country": "India", "Address": "", "Address_2": "", "address_3": "", "postal_code": "", "city": "Rajkot", "state": "Gujarat", "state": "Gujarat", "packages_per_day": "5"}' \
    -H "Content-Type: application/json"
    ```

   {"response":{"CodeDeliveryDetails":{"AttributeName":"email","DeliveryMedium":"EMAIL","Destination":"v***@o***.com"},"
   ResponseMetadata":{"HTTPHeaders":{"connection":"keep-alive","content-length":"175","content-type":"
   application/x-amz-json-1.1","date":"Mon, 14 Jun 2021 09:34:11 GMT","x-amzn-requestid":"
   0738a2ce-1234-abcd-efgh-04390a6e002e"},"HTTPStatusCode":200,"RequestId":"0738a2ce-1234-abcd-efgh-04390a6e002e","
   RetryAttempts":0},"UserConfirmed":false,"UserSub":"33acc564-abcd-1234-efgh-1b9a347c6902"},"status":1}


2. **Confirm Sign Up**
    * **URL**: `/auth/confirm_signup`
    * **Description**: To confirm the user signup, the confirmation code is sent to users email id
    * **Method**: `POST`
    * **Required Payload**:
        * `username: String`,
        * `confirmation_code: String`
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/confirm_signup" \
   -X POST \
   -d '{"username": "viraj@outliant.com", "confirmation_code": "872321"}' \
   -H "Content-Type: application/json"
   ```

   {"response":"confirm","status":1}


3. **Resend Confirmation Code**
    * **URL**: `/auth/resend_confirmation_code`
    * **Description**: Resends the confirmation code ot users email id
    * **Method**: `POST`
    * **Required Payload**:
        * `username: String`,
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/resend_confirmation_code" \
   -X POST \
   -d '{"username": "viraj@outliant.com"}' \
   -H "Content-Type: application/json"
   ```

   {"response":{"CodeDeliveryDetails":{"AttributeName":"email","DeliveryMedium":"EMAIL","Destination":"v***@o***.com"},"
   ResponseMetadata":{"HTTPHeaders":{"connection":"keep-alive","content-length":"104","content-type":"
   application/x-amz-json-1.1","date":"Mon, 14 Jun 2021 09:52:05 GMT","x-amzn-requestid":"
   b14318e4-1234-abcd-efgh-a4c0b761fc40"},"HTTPStatusCode":200,"RequestId":"b14318e4-abcd-1234-efgh-a4c0b761fc40","
   RetryAttempts":0}},"status":1}


4. **Sign In**
    * **URL**: `/auth/signin`
    * **Description**: To Sign in the user with username and password
    * **Method**: `POST`
    * **Required Payload**:
        * `username: String`,
        * `password: String`
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/signin" \
   -X POST \
   -d '{"username": "viraj@outliant.com", "password": "Abcd@1234"}' \
   -H "Content-Type: application/json"
   ```

   {"response":{"AuthenticationResult":{"AccessToken":"ACCESS TOKEN","ExpiresIn":3600,"IdToken":"ID TOKEN","
   RefreshToken":"REFRESH TOKEN","TokenType":"Bearer"},"ChallengeParameters":{},"ResponseMetadata":{"HTTPHeaders":{"
   connection":"keep-alive","
   content-length":"4218","content-type":"application/x-amz-json-1.1","date":"Mon, 14 Jun 2021 09:57:13 GMT","
   x-amzn-requestid":"8b7b741c-1234-ABCD-EFGH-5b6c52328032"},"HTTPStatusCode":200,"RequestId":"
   8b7b741c-1234-ABCD-EFGH-5b6c52328032","RetryAttempts":0}},"status":1}


5. **Change Password**
    * **URL**: `/auth/change_password`
    * **Description**: To change the old password
    * **Method**: `POST`
    * **Required Payload**:
        * `current_password: String`,
        * `new_password: String`
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/change_password" \
   -X POST \
   -d '{"current_password": "Abcd@1234", "new_password": "Abcd@12345"}' \
   -H "Content-Type: application/json" \
   -H "X-LSO-Authorization: Bearer ACCESS TOKEN"
   ```

   {"response":"Changed","status":1}


6. **Forgot Password**
    * **URL**: `/auth/forgot_password`
    * **Description**: If user forgot their password, the confirmation code is sent to users email id
    * **Method**: `POST`
    * **Required Payload**:
        * `username: String`
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/forgot_password" \
   -X POST \
   -d '{"username": "viraj@outliant.com"}' \
   -H "Content-Type: application/json"
   ```

   {"response":{"CodeDeliveryDetails":{"AttributeName":"email","DeliveryMedium":"EMAIL","Destination":"v***@o***.com"},"
   ResponseMetadata":{"HTTPHeaders":{"connection":"keep-alive","content-length":"104","content-type":"
   application/x-amz-json-1.1","date":"Mon, 14 Jun 2021 10:12:11 GMT","x-amzn-requestid":"
   f119b929-1234-abcd-efgh-27e14fb4b33b"},"HTTPStatusCode":200,"RequestId":"f119b929-1234-abcd-efgh-27e14fb4b33b","
   RetryAttempts":0}},"status":1}


7. **Confirm Forgot Password**
    * **URL**: `/auth/confirm_forgot_password`
    * **Description**: To confirm the code and create new password
    * **Method**: `POST`
    * **Required Payload**:
        * `username: String`,
        * `confirmation_code: String`,
        * `password: String`
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/confirm_forgot_password" \
   -X POST \
   -d '{"username": "viraj@outliant.com", "confirmation_code": "675628", "password": "Abcd@1234"}' \
   -H "Content-Type: application/json"
   ```

   {"response":"Changed","status":1}


8. **Global Sign Out**
    * **URL**: `/auth/global_sign_out`
    * **Description**: To sign out from all the devices
    * **Method**: `GET`
    * **Required Payload**: None
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/global_sign_out" \
   -H "X-LSO-Authorization: Bearer ACCESS TOKEN"
   ```

   {"response": "Sign out", "status": 1 }


9. **Update Profile**
    * **URL**: `/auth/update_profile`
    * **Description**: To update the user profile
    * **Method**: `POST`
    * **Required Payload**:
        * `old_email: String`,
        * `new_email: String`
    * **Return Type**: JSON
    * **Sample cURL**:
   ```
   $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/update_profile" \
   -X POST \
   -d '{"old_email": "viraj@outliant.com", "new_email": "yimagal913@beydent.com"}' \
   -H "X-LSO-Authorization: Bearer ACCESS TOKEN" \
   -H "Content-Type: application/json"
   ```

   {"response": {"
   CodeDeliveryDetailsList": [{"AttributeName": "email","DeliveryMedium": "EMAIL","Destination": "y***@b***.com"}],"
   ResponseMetadata": {"HTTPHeaders": {"connection": "keep-alive","content-length": "110","content-type": "
   application/x-amz-json-1.1","date": "Wed, 16 Jun 2021 07:19:36 GMT","x-amzn-requestid": "
   3c9a5f37-5826-4aa9-a8a7-0e888f2a08bc"},"HTTPStatusCode": 200,"RequestId": "3c9a5f37-5826-4aa9-a8a7-0e888f2a08bc","
   RetryAttempts": 0 } },"status": 1 }


10. **Verify User Attribute**
    * **URL**: `/auth/verify_user_attribute`
    * **Description**: To verify the updated attribute
    * **Method**: `POST`
    * **Required Payload**:
        * `verification_code: String`,
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/verify_user_attribute" \
    -X POST \
    -d '{"verification_code": "108547"}' \
    -H "X-LSO-Authorization: Bearer ACCESS TOKEN" \
    -H "Content-Type: application/json"
    ```

    {"response": "Verified","status": 1 }


11. **Add Address**
    * **URL**: `addressbook/add_address`
    * **Description**: To add addresses
    * **Method**: `POST`
    * **Required Payload**:
        * `quickcode: String`,
        * `name: String`,
        * `phone: String`,
        * `company: String`,
        * `address: String`,
        * `city: String`,
        * `state: String`,
        * `country: String`,
        * `zip: String`,
        * `billing_ref": String`
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/addressbook/add_address" \
    -X POST \
    -d '{"quickcode": "1234", "name": "test", "phone": "0123456789", "company": "outliant", "address": "12th st n", "city": "Austin", "state": "TX", "country": "US", "zip_code": "73301", "billing_ref": ""}' \
    -H "Content-Type: application/json" \
    -H "x-LSO-Authorization: Bearer ACCESS TOKEN"
    ```

    {
    "status": 1,
    "response": {
    "quickcode": "1234",
    "name": "test",
    "phone": "0123456789",
    "company": "outliant",
    "address": "12th st n",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "zip": "73301",
    "billing_ref": ""
    } }


12. **Import Address**
    * **URL**: `addressbook/import_address`
    * **Description**: It imports the address via csv file
    * **Method**: `POST`
    * **Required Payload**:
        * `file: File`
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/addressbook/import_address" \
    -X POST \
    -F 'file=@test.csv' \
    -H "Content-Type: multipart/form-data" \
    -H "X-LSO-Authorization: Bearer ACCESS TOKEN"
    ```

    {
    "status": 1,
    "response": [
    {
    "quickcode": "123",
    "name": "Test",
    "phone": "0123456789",
    "company": "Test",
    "address": "6800 12TH ST N",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "zip_code": "73301",
    "billing_ref": ""
    }, {
    "quickcode": "124",
    "name": "Test1",
    "phone": "0123456789",
    "company": "Test1",
    "address": "6800 12TH ST N",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "zip_code": "73301",
    "billing_ref": ""
    }
    ]
    }


13. **Create Group**
    * **URL**: `group_maintenance/create_group`
    * **Description**: It creates the group
    * **Method**: `POST`
    * **Required Payload**:
        * `group_name: String`,
        * `group_description: String`
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/group_maintenance/create_group" \
    -X POST \
    -d '{"group_name": "Latest", "group_description": "Latest Group"}' \
    -H "Content-Type: application/json" \
    -H "X-LSO-Authorization: Bearer ACCESS TOKEN"
    ```

    {
    "status": 1,
    "response": {
    "group_name": "Latest",
    "group_description": "Latest Group"
    } }


14. **Ship With Account**
    * **URL**: `ship/ship_with_account`
    * **Description**: To ship something with account
    * **Methods**: `POST`
    * **Required Payload**:
        * `from_to_quick_code: String`
        * `from_name: String`
        * `from_phone: String`
        * `from_company: String`
        * `from_address_1: String`
        * `from_address_2: String`
        * `from_city: String`
        * `from_state: String`
        * `from_zip: String`
        * `from_country: String`
        * `from_is_residential_address: String`
        * `to_to_quick_code: String`
        * `to_name: String`
        * `to_phone: String`
        * `to_company: String`
        * `to_address_1: String`
        * `to_address_2: String`
        * `to_city: String`
        * `to_state: String`
        * `to_zip: String`
        * `to_country: String`
        * `to_is_residential_address: String`
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/ship/ship_with_account" \
    -X POST \
    -H "X-LSO-Authorization: Bearer ACCESS TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"from_to_quick_code": "1234", "from_name": "Anthony", "from_phone": "5164760176", "from_company": "Outliant", "from_address_1": "3600 S IH", "from_address_2": "Frontgate RD S", "from_city": "Austin", "from_state": "TX", "from_zip": "78704", "from_country": "US", "from_is_residential_address": "true", "to_to_quick_code": "1234", "to_name": "Anthony", "to_phone": "5164760176", "to_company": "Outliant", "to_address_1": "3600 S IH", "to_address_2": "Frontgate RD S", "to_city": "Austin", "to_state": "TX", "to_zip": "78704", "to_country": "US", "to_is_residential_address": "true"}'
    ```

    {
    "status": 1,
    "response": {
    "from_to_quick_code": "1234",
    "from_name": "Anthony",
    "from_phone": "5164760176",
    "from_company": "Outliant",
    "from_address_1": "3600 S IH",
    "from_address_2": "Frontgate RD S",
    "from_city": "Austin",
    "from_state": "TX",
    "from_zip": "78704",
    "from_country": "US",
    "from_is_residential_address": "true",
    "to_to_quick_code": "1234",
    "to_name": "Anthony",
    "to_phone": "5164760176",
    "to_company": "Outliant",
    "to_address_1": "3600 S IH",
    "to_address_2": "Frontgate RD S",
    "to_city": "Austin",
    "to_state": "TX",
    "to_zip": "78704",
    "to_country": "US",
    "to_is_residential_address": "true"
    } }


15. **Add User Signup**
    * **URL**: `auth/add_user_signup`
    * **Description**: To add users into account
    * **Methods**L `POST`
    * **Reuired Payload**:
        * `account_number: String`
        * `username: String`
        * `password: String`
        * `confirm_password: String`
        * `first_name: String`
        * `last_name: String`
        * `company_name: String`
        * `company_phone: String`
        * `address: String`
        * `address_2: String`
        * `city: String`
        * `state: String`
        * `zip_code: String`
    * **Return Type**: JSON
    * **Sample cURL**:
    ```
    $ curl "http://lsobackend-dev.us-west-2.elasticbeanstalk.com/auth/add_user_signup" \
    -X POST \
    -H "X-LSO-Authorization: Bearer ACCESS TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"account_number": "12345", "username": "nanicon255@gamezalo.com", "password": "Abcd@1234", "confirm_password": "Abcd@1234", "first_name": "nani", "last_name": "con", "company_name": "Outliant", "company_phone": "0987654321", "address": "3600 S IH", "address_2": "Frontgate RD S", "city": "Austin", "state": "TX", "zip_code": "78704"}'
    ```

    {
    "status": 1,
    "response": {
    "UserConfirmed": false,
    "CodeDeliveryDetails": {
    "Destination": "n***@g***.com",
    "DeliveryMedium": "EMAIL",
    "AttributeName": "email"
    },
    "UserSub": "233c8856-775c-4af1-8ccb-891ceb293502",
    "ResponseMetadata": {
    "RequestId": "fafd995c-33fb-428a-a963-4913fffe3efb",
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
    "date": "Wed, 30 Jun 2021 07:36:21 GMT",
    "content-type": "application/x-amz-json-1.1",
    "content-length": "175",
    "connection": "keep-alive",
    "x-amzn-requestid": "fafd995c-33fb-428a-a963-4913fffe3efb"
    },
    "RetryAttempts": 0 } } }