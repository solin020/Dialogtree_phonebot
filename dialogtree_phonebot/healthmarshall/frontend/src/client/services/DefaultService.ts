/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnnotatedDocument } from '../models/AnnotatedDocument';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class DefaultService {

    /**
     * Process Doc
     * @param doc
     * @returns AnnotatedDocument Successful Response
     * @throws ApiError
     */
    public static processDocProcessDocPost(
        doc: string,
        patient:string,
    ): CancelablePromise<AnnotatedDocument> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/process-doc',
            query: {
                'doc': doc,
                'patient': patient,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }

}
