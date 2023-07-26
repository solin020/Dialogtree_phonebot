/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CallLog } from '../models/CallLog';
import type { CallLogHeader } from '../models/CallLogHeader';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class DefaultService {

    /**
     * Stream Conversation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamConversationStreamConversationPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/stream-conversation',
        });
    }

    /**
     * Api Call Log
     * @param callSid
     * @returns CallLog Successful Response
     * @throws ApiError
     */
    public static apiCallLogApiCallLogCallSidGet(
        callSid: string,
    ): CancelablePromise<CallLog> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/call-log/{call_sid}',
            path: {
                'call_sid': callSid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Api Call List
     * @returns CallLogHeader Successful Response
     * @throws ApiError
     */
    public static apiCallListApiCallListGet(): CancelablePromise<Array<CallLogHeader>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/call-list',
        });
    }

}
