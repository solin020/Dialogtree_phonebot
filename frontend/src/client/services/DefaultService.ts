/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CallLog } from '../models/CallLog';
import type { CallLogHeader } from '../models/CallLogHeader';
import type { Participant } from '../models/Participant';
import type { ScheduledCall } from '../models/ScheduledCall';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class DefaultService {

    /**
     * Call Status
     * @returns any Successful Response
     * @throws ApiError
     */
    public static callStatusCallStatusPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/call-status',
        });
    }

    /**
     * Schedule Call
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static scheduleCallScheduleCallPost(
        requestBody: ScheduledCall,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/schedule-call',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Post Schedule Calls
     * @param phoneNumber
     * @param startDate
     * @param endDate
     * @param morningTime
     * @param afternoonTime
     * @param eveningTime
     * @param morningMinute
     * @param afternoonMinute
     * @param eveningMinute
     * @returns any Successful Response
     * @throws ApiError
     */
    public static postScheduleCallsScheduleCallsPost(
        phoneNumber: string,
        startDate: string,
        endDate: string,
        morningTime: number,
        afternoonTime: number,
        eveningTime: number,
        morningMinute: number,
        afternoonMinute: number,
        eveningMinute: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/schedule_calls',
            query: {
                'phone_number': phoneNumber,
                'start_date': startDate,
                'end_date': endDate,
                'morning_time': morningTime,
                'afternoon_time': afternoonTime,
                'evening_time': eveningTime,
                'morning_minute': morningMinute,
                'afternoon_minute': afternoonMinute,
                'evening_minute': eveningMinute,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Cancel Call
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelCallCancelCallPost(
        requestBody: ScheduledCall,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/cancel-call',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Cancel Schedule Calls
     * @param phoneNumber
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelScheduleCallsCancelCallsPost(
        phoneNumber: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/cancel-calls',
            query: {
                'phone_number': phoneNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * List Schedule Calls
     * @param phoneNumber
     * @returns ScheduledCall Successful Response
     * @throws ApiError
     */
    public static listScheduleCallsListScheduledCallsGet(
        phoneNumber: string,
    ): CancelablePromise<Array<ScheduledCall>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/list-scheduled-calls',
            query: {
                'phone_number': phoneNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Add Participant
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static addParticipantAddParticipantPost(
        requestBody: Participant,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/add-participant',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Delete Participant
     * @param participantStudyId
     * @param phoneNumber
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteParticipantDeleteParticipantPost(
        participantStudyId: string,
        phoneNumber: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/delete-participant',
            query: {
                'participant_study_id': participantStudyId,
                'phone_number': phoneNumber,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Api Call Log
     * @param callSid
     * @returns CallLog Successful Response
     * @throws ApiError
     */
    public static apiCallLogApiCallLogGet(
        callSid: string,
    ): CancelablePromise<CallLog> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/call-log',
            query: {
                'call_sid': callSid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Api Call List
     * @param participantStudyId
     * @returns CallLogHeader Successful Response
     * @throws ApiError
     */
    public static apiCallListApiCallListGet(
        participantStudyId: string,
    ): CancelablePromise<Array<CallLogHeader>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/call-list',
            query: {
                'participant_study_id': participantStudyId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

    /**
     * Api Participant List
     * @returns Participant Successful Response
     * @throws ApiError
     */
    public static apiParticipantListApiParticipantListGet(): CancelablePromise<Array<Participant>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/participant-list',
        });
    }

    /**
     * Read Index1
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readIndex1Get(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }

    /**
     * Read Index2
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readIndex2FaviconIcoGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/favicon.ico',
        });
    }

}
