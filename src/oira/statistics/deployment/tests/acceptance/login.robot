*** Settings ***
Library           SeleniumLibrary
Library  DebugLibrary

Test Teardown  Close Browser

*** Variables ***
${LOGIN_URL}        http://localhost:3001
${LOGIN_NAME}       admin@syslab.com
${LOGIN_PASSWORD}   secret
${BROWSER}          Chrome

*** Test Cases ***
User can log in
    When I open the login page
     And I enter the credentials  ${LOGIN_NAME}  ${LOGIN_PASSWORD}
    Then I see the navigation bar
    

*** Keywords ***
I open the login page
    Open Browser  ${LOGIN_URL}  ${BROWSER}
    Wait until page contains element  xpath=//button/div/div[text()='Sign in']
    Title Should Be  Login · Metabase

I enter the credentials
    [Arguments]  ${username}  ${password}
    Input Text  css=#formField-username input  ${username}
    Input Text  css=#formField-password input  ${password}
    Click Button  css=button[type=submit]

I see the navigation bar
    Wait Until Page Contains Element  css=div.Nav
